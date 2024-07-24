import os
import boto3
from common import logger


def handler(event, context):
    if event is not None:
        logger.info('running on AWS env')
    else:
        logger.info('running on local env')

    s3 = boto3.client('s3')
    csv_files_path = os.environ.get('ROBOCLIMATE_CSV_FILES_PATH')
    s3_bucket_name = os.environ.get('S3_BUCKET_NAME')
    s3_prefix = "backup"

    # iterate over the files of EFS folder to copy them to S3
    for file in os.listdir(csv_files_path):
        if file.endswith('.csv'):
            file_path = os.path.join(csv_files_path, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read()
            s3_key = os.path.join(s3_prefix, file)
            logger.info('writing object %s in bucket %s', s3_key, s3_bucket_name)
            s3.put_object(Body=data, Bucket=s3_bucket_name, Key=s3_key)


# when running on AWS env, __name__ = file name specified in AWS runtime's handler
if __name__ == '__main__':
    handler(None, None)
