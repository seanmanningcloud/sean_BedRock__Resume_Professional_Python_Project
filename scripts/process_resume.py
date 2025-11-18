#!/usr/bin/env python3
import os
import json
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError


# Helper Function for Bedrock
def call_bedrock_for_html(bedrock_client, model_id: str, markdown: str) -> str:
    """
    Uses Bedrock to convert Markdown resume file to ATS-optimized HTML resume.
    """
    prompt = (
        "You are an expert resume formatter. Convert the following Markdown resume "
        "into a single clean, ATS-friendly HTML page. Use semantic HTML, <section>, "
        "<h1>-<h3>, <ul>/<li>, and basic inline styles, but no external CSS or JS. "
        "Return ONLY the HTML, no explanations.\n\n"
        "Markdown resume:\n"
        "```markdown\n"
        f"{markdown}\n"
        "```"
    )

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 3000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ],
            }
        ]
    }

    response = bedrock_client.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    payload = json.loads(response["body"].read())
    html = payload["content"][0]["text"]
    return html.strip()


def call_bedrock_for_analytics(bedrock_client, model_id: str, markdown: str) -> dict:
    """
    Analyze resume and return constrained JSON.
    """
    prompt = (
        "You are an Applicant Tracking System (ATS) assistant. Analyze the resume "
        "below and return a STRICT JSON object ONLY, with this exact schema:\n\n"
        "{\n"
        '  "ats_score": <number between 0 and 100>,\n'
        '  "word_count": <integer>,\n'
        '  "keywords": [<list of important keywords found>],\n'
        '  "missing_sections": [<list of important sections that are missing>],\n'
        '  "readability_score": <number between 0 and 100>,\n'
        '  "notes": <short text summary with suggestions>\n'
        "}\n\n"
        "Do NOT include any extra text before or after the JSON.\n\n"
        "Resume in Markdown:\n"
        "```markdown\n"
        f"{markdown}\n"
        "```"
    )

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1500,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ],
            }
        ]
    }

    response = bedrock_client.invoke_model(
        modelId=model_id,
        body=json.dumps(body)
    )

    payload = json.loads(response["body"].read())
    text = payload["content"][0]["text"].strip()

    try:
        analytics = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            analytics = json.loads(text[start : end + 1])
        else:
            raise

    return analytics

# Main Function that Processes the Resume
def main():
    region = os.environ.get("AWS_REGION", "us-east-1")
    bucket_name = os.environ["BUCKET_NAME"]
    # Environment will be get from the environment variable, with default value as beta
    environment = os.environ.get("ENVIRONMENT", "beta")
    deployment_table_name = os.environ["DEPLOYMENT_TABLE_NAME"]
    analytics_table_name = os.environ["ANALYTICS_TABLE_NAME"]
    commit_sha = os.environ.get("COMMIT_SHA", "unknown-commit")

    model_id_html = os.environ["MODEL_ID_HTML"]
    model_id_analytics = os.environ["MODEL_ID_ANALYTICS"]

    resume_path = os.environ.get("RESUME_PATH", "resume.md")

    # Configuring AWS Bedrock
    bedrock_client = boto3.client("bedrock-runtime", region_name=region)
    s3_client = boto3.client("s3", region_name=region)
    dynamodb = boto3.resource("dynamodb", region_name=region)

    deployment_table = dynamodb.Table(deployment_table_name)
    analytics_table = dynamodb.Table(analytics_table_name)

    # loading the resume file from local path
    with open(resume_path, "r", encoding="utf-8") as f:
        resume_markdown = f.read()

    # Calling Bedrock to generate HTML
    print("Calling Bedrock to generate HTML...")
    html_content = call_bedrock_for_html(bedrock_client, model_id_html, resume_markdown)

    # Calling Bedrock to generate ATS analytics
    print("Calling Bedrock to generate ATS analytics...")
    analytics = call_bedrock_for_analytics(
        bedrock_client, model_id_analytics, resume_markdown
    )

    # Copying HTML to S3 Bucket
    object_key = f"{environment}/index.html"
    print(f"Uploading HTML to s3://{bucket_name}/{object_key} ...")

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=html_content.encode("utf-8"),
            ContentType="text/html; charset=utf-8",
        )
    except ClientError as e:
        print(f"Failed to upload HTML to S3: {e}")
        raise

    s3_url = f"s3://{bucket_name}/{object_key}"
    timestamp = datetime.now(timezone.utc).isoformat()
    deployment_id = f"{commit_sha}-{environment}-{uuid.uuid4()}"

    # Writing deployment metadata to DynamoDB DeploymentTracking table
    print("Writing deployment metadata to DynamoDB DeploymentTracking table...")
    deployment_item = {
        "deploymentId": deployment_id,
        "commitSha": commit_sha,
        "environment": environment,
        "status": "SUCCESS",
        "s3Url": s3_url,
        "modelUsedHtml": model_id_html,
        "modelUsedAnalytics": model_id_analytics,
        "timestamp": timestamp,
    }

    try:
        deployment_table.put_item(Item=deployment_item)
    except ClientError as e:
        print(f"Failed to write deployment tracking record: {e}")
        raise

    # Writing ATS analytics to DynamoDB ResumeAnalytics table
    print("Writing ATS analytics to DynamoDB ResumeAnalytics table...")
    analytics_item = {
        "commitSha": commit_sha,
        "environment": environment,
        "timestamp": timestamp,
        "ats_score": analytics.get("ats_score"),
        "word_count": analytics.get("word_count"),
        "keywords": analytics.get("keywords"),
        "missing_sections": analytics.get("missing_sections"),
        "readability_score": analytics.get("readability_score"),
        "notes": analytics.get("notes"),
    }

    try:
        analytics_table.put_item(Item=analytics_item)
    except ClientError as e:
        print(f"Failed to write analytics record: {e}")
        raise

    print("Processing complete.")
    print(f"Website URL (S3 object): {s3_url}")


if __name__ == "__main__":
    main()
