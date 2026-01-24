# GitHub Actions Secrets Setup Guide

This document outlines all the secrets that need to be configured in your GitHub repository for the CI/CD workflows to function properly.

## How to Add Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter the secret name and value
5. Click **Add secret**

---

## Required Secrets

### AWS Authentication (Choose ONE method)

#### Option 1: OIDC Authentication (Recommended)
Provides more secure, keyless authentication without storing long-lived credentials.

- **`AWS_ROLE_ARN`** - ARN of the AWS IAM role for production deployments
  - Format: `arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME`
  - Required for: Main deployment workflows

- **`AWS_ROLE_ARN_DEV`** - ARN of the AWS IAM role for dev environment deployments
  - Format: `arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME_DEV`
  - Required for: Dev environment deployments

#### Option 2: Access Key Authentication
Less secure than OIDC but simpler for getting started.

- **`AWS_ACCESS_KEY_ID`** - AWS access key ID
  - Required for: AWS API authentication

- **`AWS_SECRET_ACCESS_KEY`** - AWS secret access key
  - **⚠️ Handle with care!** This is sensitive - rotate regularly
  - Required for: AWS API authentication

---

### Terraform Backend Configuration

- **`TF_STATE_BUCKET`** - S3 bucket name for storing Terraform state
  - Format: `my-terraform-state-bucket`
  - Required for: Terraform state management

- **`TF_LOCK_TABLE`** - DynamoDB table name for Terraform state locking
  - Format: `terraform-lock-table`
  - Required for: Preventing concurrent Terraform runs

---

## Optional Secrets

### Cost Estimation

- **`INFRACOST_API_KEY`** - API key for Infracost service
  - Get from: https://www.infracost.io/
  - Used for: Infrastructure cost estimation in PRs
  - Optional: Omit if you don't want cost estimation

### Notifications

- **`SLACK_WEBHOOK_URL`** - Slack webhook URL for notifications
  - Format: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`
  - Used for: Sending deployment and build notifications to Slack
  - Optional: Omit if you don't use Slack

---

## Security Best Practices

1. **Use OIDC when possible** - Eliminates need for long-lived credentials
2. **Rotate access keys regularly** - If using access key method
3. **Limit IAM permissions** - Use least privilege principle for IAM roles
4. **Encrypt sensitive data** - Ensure S3 and DynamoDB are encrypted
5. **Audit access** - Monitor secret usage in GitHub Actions logs
6. **Never commit secrets** - Ensure `.gitignore` excludes sensitive files

---

## Verification

After adding secrets, you can verify they're set up correctly by:
1. Running the security scan workflow manually
2. Checking the Actions tab for any authentication errors
3. Ensuring infrastructure deployments complete successfully

---

## Troubleshooting

If workflows fail with authentication errors:
- Verify all required secrets are added
- Check that secret names match exactly (case-sensitive)
- Ensure IAM roles have the necessary permissions
- Check S3 bucket and DynamoDB table exist and are accessible
