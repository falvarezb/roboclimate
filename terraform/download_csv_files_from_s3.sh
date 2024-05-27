#!/bin/bash

# USAGE: ./download_csv_files_from_s3.sh <AWS_PROFILE> <CSV_FOLDER>

S3_PROFILE="$1"
if [ $# -gt 1 ]; then
    CSV_FOLDER="$2"
else
    CSV_FOLDER="$ROBOCLIMATE_CSV_FILES_PATH"
fi

aws --profile "$S3_PROFILE" s3 cp s3://roboclimate/backup "$CSV_FOLDER" --recursive
