#!/bin/bash
# Cleanup script for OpenRepoWiki AWS resources
# Run this to delete orphaned resources before terraform apply

set -e

# Disable AWS CLI pager
export AWS_PAGER=""

PROFILE="${AWS_PROFILE:-deploy}"
REGION="${AWS_REGION:-us-east-1}"
PROJECT="OpenRepoWiki"
ENV="prod"

echo "Using AWS Profile: $PROFILE"
echo "Using AWS Region: $REGION"
echo ""

# Function to safely delete a resource
safe_delete() {
    echo "Attempting: $1"
    eval "$2" 2>/dev/null || echo "  -> Already deleted or doesn't exist"
}

echo "=== Deleting Secrets Manager Secrets ==="
safe_delete "Force delete github-token secret" \
    "aws secretsmanager delete-secret --secret-id ${PROJECT}-${ENV}/github-token --force-delete-without-recovery --profile $PROFILE --region $REGION"
safe_delete "Force delete llm-api-key secret" \
    "aws secretsmanager delete-secret --secret-id ${PROJECT}-${ENV}/llm-api-key --force-delete-without-recovery --profile $PROFILE --region $REGION"

echo ""
echo "=== Deleting Lambda Functions ==="
safe_delete "Delete jobs-handler Lambda" \
    "aws lambda delete-function --function-name ${PROJECT}-${ENV}-jobs-handler --profile $PROFILE --region $REGION"
safe_delete "Delete repos-handler Lambda" \
    "aws lambda delete-function --function-name ${PROJECT}-${ENV}-repos-handler --profile $PROFILE --region $REGION"

echo ""
echo "=== Deleting CloudWatch Log Groups ==="
safe_delete "Delete jobs-handler logs" \
    "aws logs delete-log-group --log-group-name /aws/lambda/${PROJECT}-${ENV}-jobs-handler --profile $PROFILE --region $REGION"
safe_delete "Delete repos-handler logs" \
    "aws logs delete-log-group --log-group-name /aws/lambda/${PROJECT}-${ENV}-repos-handler --profile $PROFILE --region $REGION"
safe_delete "Delete ECS processor logs" \
    "aws logs delete-log-group --log-group-name /ecs/${PROJECT}-${ENV}-processor --profile $PROFILE --region $REGION"
safe_delete "Delete Step Functions logs" \
    "aws logs delete-log-group --log-group-name /aws/states/${PROJECT}-${ENV}-processor --profile $PROFILE --region $REGION"
safe_delete "Delete API Gateway logs" \
    "aws logs delete-log-group --log-group-name /aws/apigateway/${PROJECT}-${ENV}-api --profile $PROFILE --region $REGION"
safe_delete "Delete WAF logs (regional)" \
    "aws logs delete-log-group --log-group-name aws-waf-logs-${PROJECT}-${ENV} --profile $PROFILE --region $REGION"
safe_delete "Delete WAF logs (us-east-1 for CloudFront)" \
    "aws logs delete-log-group --log-group-name aws-waf-logs-${PROJECT}-${ENV} --profile $PROFILE --region us-east-1"

echo ""
echo "=== Deleting IAM Roles ==="
# Need to detach policies and delete inline policies first
for ROLE in "${PROJECT}-${ENV}-ecs-task" "${PROJECT}-${ENV}-ecs-task-execution" "${PROJECT}-${ENV}-lambda-execution" "${PROJECT}-${ENV}-sfn-execution"; do
    echo "Processing role: $ROLE"
    
    # List and detach managed policies
    POLICIES=$(aws iam list-attached-role-policies --role-name $ROLE --profile $PROFILE --query 'AttachedPolicies[].PolicyArn' --output text 2>/dev/null || echo "")
    for POLICY in $POLICIES; do
        safe_delete "  Detach policy $POLICY" \
            "aws iam detach-role-policy --role-name $ROLE --policy-arn $POLICY --profile $PROFILE"
    done
    
    # List and delete inline policies
    INLINE_POLICIES=$(aws iam list-role-policies --role-name $ROLE --profile $PROFILE --query 'PolicyNames[]' --output text 2>/dev/null || echo "")
    for POLICY in $INLINE_POLICIES; do
        safe_delete "  Delete inline policy $POLICY" \
            "aws iam delete-role-policy --role-name $ROLE --policy-name $POLICY --profile $PROFILE"
    done
    
    # Delete the role
    safe_delete "  Delete role $ROLE" \
        "aws iam delete-role --role-name $ROLE --profile $PROFILE"
done

echo ""
echo "=== Deleting DynamoDB Tables ==="
safe_delete "Delete main table" \
    "aws dynamodb delete-table --table-name ${PROJECT}-${ENV}-main --profile $PROFILE --region $REGION"
safe_delete "Delete jobs table" \
    "aws dynamodb delete-table --table-name ${PROJECT}-${ENV}-jobs --profile $PROFILE --region $REGION"

echo ""
echo "=== Deleting S3 Bucket ==="
BUCKET_NAME=$(echo "${PROJECT}-artifacts-${ENV}" | tr '[:upper:]' '[:lower:]')
echo "Emptying bucket: $BUCKET_NAME"
aws s3 rm s3://$BUCKET_NAME --recursive --profile $PROFILE --region $REGION 2>/dev/null || echo "  -> Bucket empty or doesn't exist"
safe_delete "Delete bucket $BUCKET_NAME" \
    "aws s3api delete-bucket --bucket $BUCKET_NAME --profile $PROFILE --region $REGION"

echo ""
echo "=== Deleting ECR Repository ==="
ECR_REPO=$(echo "${PROJECT}-${ENV}-processor" | tr '[:upper:]' '[:lower:]')
safe_delete "Delete ECR repository $ECR_REPO" \
    "aws ecr delete-repository --repository-name $ECR_REPO --force --profile $PROFILE --region $REGION"

echo ""
echo "=== Deleting KMS Alias ==="
safe_delete "Delete KMS alias" \
    "aws kms delete-alias --alias-name alias/${PROJECT}-${ENV}-s3 --profile $PROFILE --region $REGION"

echo ""
echo "=== Deleting CloudFront Distribution ==="
# Find and disable/delete CloudFront distribution
CF_ID=$(aws cloudfront list-distributions --profile $PROFILE --query "DistributionList.Items[?Comment=='OpenRepoWiki Static UI - ${ENV}'].Id" --output text 2>/dev/null || echo "")
if [ -n "$CF_ID" ] && [ "$CF_ID" != "None" ]; then
    echo "Found CloudFront distribution: $CF_ID"
    
    # Get current config and ETag
    ETAG=$(aws cloudfront get-distribution --id $CF_ID --profile $PROFILE --query 'ETag' --output text 2>/dev/null || echo "")
    ENABLED=$(aws cloudfront get-distribution --id $CF_ID --profile $PROFILE --query 'Distribution.DistributionConfig.Enabled' --output text 2>/dev/null || echo "")
    
    if [ "$ENABLED" = "True" ] || [ "$ENABLED" = "true" ]; then
        echo "  Disabling distribution..."
        aws cloudfront get-distribution-config --id $CF_ID --profile $PROFILE --output json > /tmp/cf-config.json
        cat /tmp/cf-config.json | python3 -c "import json,sys; d=json.load(sys.stdin); d['DistributionConfig']['Enabled']=False; print(json.dumps(d['DistributionConfig']))" > /tmp/cf-config-disabled.json
        aws cloudfront update-distribution --id $CF_ID --if-match $ETAG --distribution-config file:///tmp/cf-config-disabled.json --profile $PROFILE --output text --query 'Distribution.Status'
        
        echo "  Waiting for distribution to be disabled (this may take 5-15 minutes)..."
        while true; do
            STATUS=$(aws cloudfront get-distribution --id $CF_ID --profile $PROFILE --query 'Distribution.Status' --output text 2>/dev/null || echo "")
            if [ "$STATUS" = "Deployed" ]; then
                break
            fi
            echo "    Status: $STATUS - waiting..."
            sleep 30
        done
        ETAG=$(aws cloudfront get-distribution --id $CF_ID --profile $PROFILE --query 'ETag' --output text 2>/dev/null || echo "")
    fi
    
    safe_delete "Delete CloudFront distribution" \
        "aws cloudfront delete-distribution --id $CF_ID --if-match $ETAG --profile $PROFILE"
fi

echo ""
echo "=== Deleting WAF Web ACLs ==="
# Regional WAF
WAF_ID=$(aws wafv2 list-web-acls --scope REGIONAL --profile $PROFILE --region $REGION --query "WebACLs[?Name=='${PROJECT}-${ENV}-waf'].Id" --output text 2>/dev/null || echo "")
if [ -n "$WAF_ID" ] && [ "$WAF_ID" != "None" ]; then
    LOCK_TOKEN=$(aws wafv2 get-web-acl --name "${PROJECT}-${ENV}-waf" --scope REGIONAL --id $WAF_ID --profile $PROFILE --region $REGION --query 'LockToken' --output text 2>/dev/null || echo "")
    if [ -n "$LOCK_TOKEN" ]; then
        safe_delete "Delete regional WAF" \
            "aws wafv2 delete-web-acl --name ${PROJECT}-${ENV}-waf --scope REGIONAL --id $WAF_ID --lock-token $LOCK_TOKEN --profile $PROFILE --region $REGION"
    fi
fi

# CloudFront WAF (must be in us-east-1)
WAF_ID=$(aws wafv2 list-web-acls --scope CLOUDFRONT --profile $PROFILE --region us-east-1 --query "WebACLs[?Name=='${PROJECT}-${ENV}-waf'].Id" --output text 2>/dev/null || echo "")
if [ -n "$WAF_ID" ] && [ "$WAF_ID" != "None" ]; then
    LOCK_TOKEN=$(aws wafv2 get-web-acl --name "${PROJECT}-${ENV}-waf" --scope CLOUDFRONT --id $WAF_ID --profile $PROFILE --region us-east-1 --query 'LockToken' --output text 2>/dev/null || echo "")
    if [ -n "$LOCK_TOKEN" ]; then
        safe_delete "Delete CloudFront WAF" \
            "aws wafv2 delete-web-acl --name ${PROJECT}-${ENV}-waf --scope CLOUDFRONT --id $WAF_ID --lock-token $LOCK_TOKEN --profile $PROFILE --region us-east-1"
    fi
fi

echo ""
echo "=== Deleting CloudFront Origin Access Control ==="
OAC_ID=$(aws cloudfront list-origin-access-controls --profile $PROFILE --query "OriginAccessControlList.Items[?Name=='${PROJECT}-${ENV}-oac'].Id" --output text 2>/dev/null || echo "")
if [ -n "$OAC_ID" ] && [ "$OAC_ID" != "None" ]; then
    ETAG=$(aws cloudfront get-origin-access-control --id $OAC_ID --profile $PROFILE --query 'ETag' --output text 2>/dev/null || echo "")
    if [ -n "$ETAG" ]; then
        safe_delete "Delete OAC" \
            "aws cloudfront delete-origin-access-control --id $OAC_ID --if-match $ETAG --profile $PROFILE"
    fi
fi

echo ""
echo "=== Deleting ECS Cluster ==="
safe_delete "Delete ECS cluster" \
    "aws ecs delete-cluster --cluster ${PROJECT}-${ENV}-cluster --profile $PROFILE --region $REGION"

echo ""
echo "=== Deleting SNS Topic ==="
SNS_ARN=$(aws sns list-topics --profile $PROFILE --region $REGION --query "Topics[?contains(TopicArn, '${PROJECT}-${ENV}')].TopicArn" --output text 2>/dev/null || echo "")
if [ -n "$SNS_ARN" ]; then
    safe_delete "Delete SNS topic" \
        "aws sns delete-topic --topic-arn $SNS_ARN --profile $PROFILE --region $REGION"
fi

echo ""
echo "=== Cleanup Complete ==="
echo "You can now run: terraform apply"
