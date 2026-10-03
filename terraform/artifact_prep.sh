#!/bin/bash

# Build and verify Lambda deployment packages.
#
# For each function: build terraform/<function>_pkg/ from its source files and its lock file
# (lambda/<lock>-requirements.txt), then verify the package inside the official Lambda image:
# import the handler in isolation and run the function's unit tests against the locked deps only.
# Stops at the first failure. See lambda/README.md for the full procedure.
#
# USAGE: ./artifact_prep.sh <weather_spider|forecast_spider|uvi_spider|backup|all>
# Requires: uv, docker

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
LAMBDA_IMAGE="public.ecr.aws/lambda/python:3.13"
UV_TARGET=(--python-platform x86_64-manylinux2014 --python-version 3.13)
TOOLS_DIR="$SCRIPT_DIR/verify_tools"
ALL_FUNCTIONS="weather_spider forecast_spider uvi_spider backup"

usage() {
    echo "USAGE: ./artifact_prep.sh <weather_spider|forecast_spider|uvi_spider|backup|all>"
    exit 1
}

# Function manifest: handler | source files | lock name | unit tests
# Handlers must match handler_name in terraform/main.tf.
manifest() {
    case "$1" in
        weather_spider)  echo "weather_spider_lambda.weather_handler|weather_spider_lambda.py common.py log_config.py|spider|tests/weather_spider_lambda_test.py" ;;
        forecast_spider) echo "forecast_spider_lambda.forecast_handler|forecast_spider_lambda.py common.py log_config.py|spider|" ;;
        uvi_spider)      echo "uvi_spider_lambda.handler|uvi_spider_lambda.py common.py log_config.py|spider|tests/uvi_spider_lambda_test.py" ;;
        backup)          echo "backup_lambda.handler|backup_lambda.py log_config.py|backup|" ;;
        *) usage ;;
    esac
}

build() {
    local fn="$1" sources="$2" lock="$3"
    local pkg="$SCRIPT_DIR/${fn}_pkg"
    rm -rf "$pkg"
    mkdir "$pkg"
    for src in $sources; do
        cp "$REPO/roboclimate/$src" "$pkg/"
    done
    # --no-deps: install exactly what is locked; an incomplete lock must fail verification, not be patched up
    uv pip install --quiet --target "$pkg" --no-deps --require-hashes "${UV_TARGET[@]}" \
        -r "$REPO/lambda/${lock}-requirements.txt"
    echo "BUILT $fn ($pkg)"
}

prepare_tools() {
    rm -rf "$TOOLS_DIR"
    uv pip install --quiet --target "$TOOLS_DIR" --no-deps --require-hashes "${UV_TARGET[@]}" \
        -r "$REPO/lambda/verify-tools-requirements.txt"
}

verify() {
    local fn="$1" handler="$2" tests="$3"
    local test_args=()
    if [ -n "$tests" ]; then
        test_args=(--tests $tests)
    fi
    docker run --rm --platform linux/amd64 \
        -v "$SCRIPT_DIR/${fn}_pkg:/var/task:ro" \
        -v "$TOOLS_DIR:/opt/verify-tools:ro" \
        -v "$REPO/tests:/src/tests:ro" \
        -v "$REPO/lambda/verify_in_image.py:/opt/verify_in_image.py:ro" \
        -e OPEN_WEATHER_API=dummy -e S3_BUCKET_NAME=dummy -e ROBOCLIMATE_CSV_FILES_PATH=/tmp \
        -e AWS_DEFAULT_REGION=eu-west-1 \
        --entrypoint python3 "$LAMBDA_IMAGE" \
        -I /opt/verify_in_image.py --handler "$handler" ${test_args[@]+"${test_args[@]}"}
}

[ $# -eq 1 ] || usage
if [ "$1" == "all" ]; then
    functions="$ALL_FUNCTIONS"
else
    manifest "$1" >/dev/null
    functions="$1"
fi

prepare_tools
for fn in $functions; do
    IFS='|' read -r handler sources lock tests <<< "$(manifest "$fn")"
    build "$fn" "$sources" "$lock"
    verify "$fn" "$handler" "$tests"
done
echo "ALL CHECKS PASSED: $functions"
