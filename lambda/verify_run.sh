#!/bin/bash
# First-run check: report on a function's real (scheduled) runs since a given UTC time.
#
# USAGE: AWS_PROFILE=myadmin lambda/verify_run.sh <weather|forecast|uvi|backup> <since: YYYY-MM-DDTHH:MM:SS UTC>
# Exit 0 when at least one run happened and no errors were logged.
set -euo pipefail

export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-eu-west-1}"
[ $# -eq 2 ] || { echo "USAGE: lambda/verify_run.sh <weather|forecast|uvi|backup> <since YYYY-MM-DDTHH:MM:SS>"; exit 1; }
fn="t_roboclimate_$1"; since="$2"

since_ms="$(python3 -c "
import datetime, sys
dt = datetime.datetime.fromisoformat(sys.argv[1]).replace(tzinfo=datetime.timezone.utc)
print(int(dt.timestamp() * 1000))" "$since")"

events="$(aws logs filter-log-events --log-group-name "/aws/lambda/$fn" --start-time "$since_ms" \
    --query 'events[].[logStreamName,message]' --output text | sed -E 's/appid=[A-Za-z0-9]+/appid=<REDACTED>/g')"

runs="$(grep -c 'REPORT RequestId' <<< "$events" || true)"
errors="$(grep -cE '\[ERROR\]|Traceback|Task timed out' <<< "$events" || true)"
writes="$(grep -cE 'writing (file|object)' <<< "$events" || true)"
target_errors="$(aws cloudwatch get-metric-statistics --namespace AWS/Scheduler --metric-name TargetErrorCount \
    --start-time "${since}Z" --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --period 3600 --statistics Sum \
    --query 'sum(Datapoints[].Sum)' --output text)"

echo "== $fn since $since UTC"
echo "versions run: $(awk -F'\t' '{print $1}' <<< "$events" | grep -oE '\[[^]]+\]' | sort -u | tr '\n' ' ')"
grep -oE 'INIT_START Runtime Version: [^[:space:]]+' <<< "$events" | sort -u || true
echo "runs=$runs writes=$writes errors=$errors scheduler_target_errors=${target_errors:-0}"
grep -E '\[ERROR\]|Traceback|Task timed out' <<< "$events" | cut -c1-200 | head -5 || true

if [ "$runs" -gt 0 ] && [ "$errors" -eq 0 ]; then echo "PASS"; else echo "FAIL"; exit 1; fi
