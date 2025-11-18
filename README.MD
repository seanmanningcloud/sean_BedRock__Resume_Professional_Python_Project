# AI-Generated Resume Website with CI/CD (AWS + Bedrock + GitHub Actions)

This project automatically turns a Markdown resume (`resume.md`) into an **ATS-optimized resume website**, analyzes it using **AI (Amazon Bedrock)**, and deploys it to **S3** with **GitHub Actions**.

It also stores deployment history and ATS analytics in **DynamoDB**, so you can track how your resume evolves over time.

---

## 🎯 Project Goals

- Convert `resume.md` → professional **HTML** using AI.
- Analyze resume for **ATS readiness** (score, word count, keywords, missing sections, readability).
- Deploy to S3 using **environments**:
  - Pull Request → `beta/` (preview)
  - `main` branch → `prod/` (production)
- Track **deployments** and **analytics** in DynamoDB.
- Use **CloudFormation** for all infrastructure (no manual console clicks).

---

## 🏗 Architecture Overview

### AWS Resources (via CloudFormation)

- **S3 Bucket**
  - Public, static website hosting
  - Versioning enabled
  - Object layout:
    - `beta/index.html`
    - `prod/index.html`

- **DynamoDB Tables**
  - `DeploymentTracking`
    - Partition key: `deploymentId` (string)
    - Stores commit SHA, environment, status, S3 URL, models used, timestamp
  - `ResumeAnalytics`
    - Partition key: `commitSha` (string)
    - Sort key: `environment` (string)
    - Stores ATS score, word count, keywords, missing sections, readability score, notes

- **IAM**
  - GitHub Actions uses an AWS user/role with permissions to:
    - Deploy CloudFormation
    - Put objects to S3
    - Read/write DynamoDB tables

---

## 🔁 CI/CD Flow

### Pull Request → Beta

1. Developer opens a **Pull Request**.
2. GitHub Actions workflow:
   - Deploys `infra.yaml` (S3 bucket + DynamoDB tables).
   - Runs `process_resume.py`:
     - AI Call #1: `resume.md` → HTML (via Bedrock).
     - AI Call #2: ATS analysis JSON (via Bedrock).
   - Uploads HTML to:  
     `s3://<BUCKET_NAME>/beta/index.html`
   - Writes:
     - Deployment record → `DeploymentTracking`
     - ATS analytics → `ResumeAnalytics`

### Main branch → Prod

1. Code is merged into `main`.
2. GitHub Actions:
   - Re-deploys `infra.yaml` (idempotent).
   - Copies:
     - `beta/index.html` → `prod/index.html`
   - Writes a **production deployment record** to `DeploymentTracking`.

---

## 🧱 Files Overview

| File                                | Purpose                                                         |
|-------------------------------------|-----------------------------------------------------------------|
| `infra.yaml`                        | CloudFormation template (S3 + DynamoDB)                         |
| `process_resume.py`                 | Reads `resume.md`, calls Bedrock, uploads HTML, writes DynamoDB |
| `promote_to_prod.py` (optional)     | Copies beta → prod and writes prod deployment record            |
| `resume_template.md`                | Template of resume in Markdown                                  |
| `resume.md`                         | Your actual resume, used as source of truth                     |
| `.github/workflows/resume_pipeline.yml` | GitHub Actions CI/CD pipeline                             |
| `requirements.txt`                  | Python dependencies (boto3, etc.)                              |

---

## 🧪 Local Testing

Before relying on CI/CD, you can test `process_resume.py` locally.

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
