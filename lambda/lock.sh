#!/bin/bash
# Regenerate the Lambda lock files: lambda/<name>.in -> lambda/<name>-requirements.txt
# Resolved for the Lambda runtime (Linux x86_64, CPython 3.13), fully pinned, with hashes.
#
# USAGE: lambda/lock.sh [extra uv pip compile options]
#   lambda/lock.sh                            # re-lock, keeping current versions where possible
#   lambda/lock.sh --upgrade                  # upgrade everything allowed by the .in files
#   lambda/lock.sh --upgrade-package requests # upgrade one package
set -euo pipefail

cd "$(dirname "$0")"

for in_file in *.in; do
    name="${in_file%.in}"
    uv pip compile "$in_file" \
        --output-file "${name}-requirements.txt" \
        --python-platform x86_64-manylinux2014 \
        --python-version 3.13 \
        --generate-hashes \
        --custom-compile-command "lambda/lock.sh" \
        --quiet \
        "$@"
    echo "locked $in_file -> ${name}-requirements.txt"
done
