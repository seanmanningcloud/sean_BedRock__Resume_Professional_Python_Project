import boto3, os, datetime

region = os.environ["AWS_REGION"]
bucket = os.environ["BUCKET_NAME"]
deployment_table = os.environ["DEPLOYMENT_TABLE_NAME"]
commit_sha = os.environ.get("COMMIT_SHA", "unknown")

s3 = boto3.client("s3", region_name=region)
dynamodb = boto3.resource("dynamodb", region_name=region)

table = dynamodb.Table(deployment_table)

# Copy resume from beta to prod
s3.copy_object(
    Bucket=bucket,
    CopySource={'Bucket': bucket, 'Key': 'beta/index.html'},
    Key='prod/index.html',
    ContentType="text/html",
)

# Update deployment tracking table
table.put_item(
    Item={
        "deploymentId": f"prod-{commit_sha}",
        "commitSha": commit_sha,
        "environment": "prod",
        "status": "SUCCESS",
        "s3Url": f"s3://{bucket}/prod/index.html",
        "timestamp": datetime.datetime.utcnow().isoformat(),
    }
)

print("Production update complete.")
