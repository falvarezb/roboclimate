#!/bin/bash
# Pre-release check: download a published Lambda version and run it in the Lambda Runtime Interface
# Emulator (official python:3.13 image) against a throwaway copy of the CSV files.
#
# USAGE: AWS_PROFILE=myadmin OPEN_WEATHER_API=... lambda/prerelease_check.sh <weather|forecast|uvi|backup> <version>
#   Spiders: real OpenWeather calls; must write every city with no [ERROR] lines.
#   Backup:  runs with no AWS credentials; must import, read the CSVs and fail only at the first S3 call.
# Seed data comes from csv_files/ (download the latest with terraform/download_csv_files_from_s3.sh first).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LAMBDA_IMAGE="public.ecr.aws/lambda/python:3.13"
PORT="${PORT:-9123}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-eu-west-1}"

[ $# -eq 2 ] || { echo "USAGE: lambda/prerelease_check.sh <weather|forecast|uvi|backup> <version>"; exit 1; }
name="$1"; version="$2"; fn="t_roboclimate_$name"
case "$name" in
    weather|forecast|uvi) csv_glob="${name}_*.csv"; : "${OPEN_WEATHER_API:?OPEN_WEATHER_API must be set}" ;;
    backup) csv_glob="*.csv"; OPEN_WEATHER_API="unused" ;;
    *) echo "unknown function: $name"; exit 1 ;;
esac

work="$(mktemp -d)"
trap 'docker rm -f "roboclimate-prerelease-$$" >/dev/null 2>&1 || true' EXIT
mkdir "$work/code" "$work/efs"

aws lambda get-function --function-name "$fn" --qualifier "$version" --output json > "$work/meta.json"
read -r handler runtime expected_sha url < <(python3 -c "
import json; d = json.load(open('$work/meta.json')); c = d['Configuration']
print(c['Handler'], c['Runtime'], c['CodeSha256'], d['Code']['Location'])")
curl -sf -o "$work/code.zip" "$url"
actual_sha="$(openssl dgst -sha256 -binary "$work/code.zip" | base64)"
echo "$fn:$version runtime=$runtime handler=$handler"
[ "$actual_sha" == "$expected_sha" ] || { echo "FAIL code hash mismatch"; exit 1; }
echo "PASS code hash matches CodeSha256"
unzip -q "$work/code.zip" -d "$work/code"
cp "$REPO"/csv_files/$csv_glob "$work/efs/"

docker run -d --name "roboclimate-prerelease-$$" --platform linux/amd64 -p "$PORT:8080" \
    -v "$work/code:/var/task:ro" -v "$work/efs:/mnt/efs" \
    -e OPEN_WEATHER_API -e S3_BUCKET_NAME=roboclimate -e ROBOCLIMATE_CSV_FILES_PATH=/mnt/efs \
    "$LAMBDA_IMAGE" "$handler" >/dev/null
for _ in $(seq 1 30); do curl -s -o /dev/null "http://localhost:$PORT/" && break; sleep 1; done
response="$(curl -s -X POST "http://localhost:$PORT/2015-03-31/functions/function/invocations" -d '{"source":"aws.scheduler"}')"
sleep 1
docker logs "roboclimate-prerelease-$$" > "$work/run.log" 2>&1
sed -i.bak "s/${OPEN_WEATHER_API}/<REDACTED>/g" "$work/run.log"

errors="$(grep -cE '^\[ERROR\]|Traceback' "$work/run.log" || true)"
writes="$(grep -c 'writing file' "$work/run.log" || true)"
echo "response=${response:0:200} errors=$errors writes=$writes (log: $work/run.log)"

if [ "$name" == "backup" ]; then
    if grep -q "ImportModuleError" "$work/run.log"; then echo "FAIL backup could not import"; exit 1; fi
    if grep -q "Unable to locate credentials" "$work/run.log" && grep -q "writing object backup/" "$work/run.log"; then
        echo "PASS backup imported, read the CSVs and stopped at the first S3 call (no credentials, as intended)"
        exit 0
    fi
    echo "FAIL backup did not reach the S3 call"; grep -E '^\[ERROR\]|Error' "$work/run.log" | head -5; exit 1
fi

failed=0
for f in "$work"/efs/$csv_glob; do
    base="$(basename "$f")"
    added=$(( $(wc -l < "$f") - $(wc -l < "$REPO/csv_files/$base") ))
    printf "  %-24s +%s rows\n" "$base" "$added"
    [ "$added" -gt 0 ] || failed=1
done
if [ "$errors" -eq 0 ] && [ "$failed" -eq 0 ]; then
    echo "PASS $fn:$version wrote every city with no errors"
else
    echo "FAIL $fn:$version"; grep -E '^\[ERROR\]|Traceback' "$work/run.log" | head -5; exit 1
fi
