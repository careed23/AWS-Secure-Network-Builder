# Secrets Configuration Checklist

Use this checklist to ensure all required secrets are properly configured in your GitHub repository.

## Steps to Add Secrets

1. Open your repository on GitHub
2. Go to **Settings** → **Secrets and variables** → **Actions**
3. Add each secret from the lists below

## ✅ Required Secrets

### AWS Authentication (Choose ONE option below)

#### Option A: OIDC Authentication (Recommended)
- [ ] `AWS_ROLE_ARN` - Production IAM role ARN
  - Used in: `terraform-deploy.yml`
  - Example: `arn:aws:iam::123456789012:role/github-actions-prod`
  
- [ ] `AWS_ROLE_ARN_DEV` - Dev IAM role ARN
  - Used in: `terraform-deploy.yml` (currently configured)
  - Example: `arn:aws:iam::123456789012:role/github-actions-dev`

#### Option B: Access Keys
- [ ] `AWS_ACCESS_KEY_ID` - AWS access key ID
  - Used in: Deploy workflows
  
- [ ] `AWS_SECRET_ACCESS_KEY` - AWS secret access key
  - Used in: Deploy workflows

### Terraform Backend
- [ ] `TF_STATE_BUCKET` - S3 bucket for Terraform state
  - Used in: `terraform-deploy.yml` and `terraform-pr.yml`
  - Example: `my-org-terraform-state`
  - Must be created before workflows run
  
- [ ] `TF_LOCK_TABLE` - DynamoDB table for state locking
  - Used in: `terraform-deploy.yml`
  - Example: `terraform-lock-table`
  - Must be created before workflows run

## ⭐ Optional Secrets

- [ ] `INFRACOST_API_KEY` - For cost estimation
  - Used in: `terraform-pr.yml` (if cost check is enabled)
  
- [ ] `SLACK_WEBHOOK_URL` - For Slack notifications
  - Used in: Deploy and failure notifications

## 📋 Workflow Secret Usage Summary

### terraform-deploy.yml
```yaml
Secrets Used:
- AWS_ROLE_ARN_DEV (AWS authentication)
- TF_STATE_BUCKET (Terraform backend)
- TF_LOCK_TABLE (Terraform locking)
```

### terraform-pr.yml
```yaml
Secrets Used:
- TF_STATE_BUCKET (Terraform init)
- TF_LOCK_TABLE (Terraform locking)
```

### security-scan.yml
```yaml
Secrets Used:
- None (this workflow doesn't require secrets)
```

## 🔐 Pre-Deployment Setup

Before activating the CI/CD workflows, ensure:

1. **AWS Account Setup**
   - [ ] Create IAM roles for OIDC or generate access keys
   - [ ] Ensure roles have necessary permissions (EC2, VPC, IAM, etc.)
   - [ ] Configure trust relationships for OIDC if using that method

2. **S3 State Bucket**
   ```bash
   aws s3api create-bucket \
     --bucket <TF_STATE_BUCKET> \
     --region us-east-1
   
   # Enable versioning
   aws s3api put-bucket-versioning \
     --bucket <TF_STATE_BUCKET> \
     --versioning-configuration Status=Enabled
   
   # Enable encryption
   aws s3api put-bucket-encryption \
     --bucket <TF_STATE_BUCKET> \
     --server-side-encryption-configuration '{
       "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
     }'
   ```

3. **DynamoDB Lock Table**
   ```bash
   aws dynamodb create-table \
     --table-name <TF_LOCK_TABLE> \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST \
     --region us-east-1
   ```

4. **GitHub Environments (Optional but Recommended)**
   - [ ] Create `dev` environment with protection rules
   - [ ] Create `prod` environment with required reviewers
   - [ ] Configure environment-specific secrets if needed

## ✨ Verification

After adding all secrets:

1. **Run Security Scan Workflow**
   - Go to Actions → Security Scanning
   - Click "Run workflow"
   - Verify it completes successfully

2. **Test with a PR**
   - Create a test branch with a minor Terraform change
   - Open a pull request
   - Verify `terraform-pr.yml` runs and completes

3. **Check Logs**
   - Review workflow logs for any authentication errors
   - Ensure Terraform init completes successfully
   - Verify plan/apply operations work as expected

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| `UnauthorizedOperation` | Check IAM role permissions |
| `NoCredentialsProvider` | Verify AWS authentication secrets are set |
| `AccessDenied` on S3 | Ensure S3 bucket exists and IAM role has `s3:*` permissions |
| `ResourceNotFoundException` for DynamoDB | Create the lock table or update table name |
| Secrets not found | Verify secret names match exactly (case-sensitive) |

## 📚 References

- [GitHub Actions Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [AWS OIDC with GitHub Actions](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Terraform AWS Backend](https://www.terraform.io/language/settings/backends/s3)
