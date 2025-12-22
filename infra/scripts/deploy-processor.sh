#!/bin/bash
set -e

REGION="us-east-1"
ACCOUNT_ID="429971482374"
ECR_REPO_NAME="openrepowiki-prod-processor"
ECR_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO_NAME}"
TIMESTAMP=$(date +%s)
IMAGE_TAG="v-${TIMESTAMP}"
IMAGE_URI="${ECR_URL}:${IMAGE_TAG}"
TASK_FAMILY="OpenRepoWiki-prod-processor"
SFN_ARN="arn:aws:states:us-east-1:429971482374:stateMachine:OpenRepoWiki-prod-processor"

echo "Logging in to ECR..."
aws ecr get-login-password --region ${REGION} --profile deploy | docker login --username AWS --password-stdin ${ECR_URL}

echo "Building and Pushing Image ${IMAGE_URI}..."
docker build -t ${ECR_REPO_NAME} -f services/processor/Dockerfile .
docker tag ${ECR_REPO_NAME}:latest ${IMAGE_URI}
docker push ${IMAGE_URI}

echo "Fetching current Task Definition..."
TASK_DEF_JSON=$(aws ecs describe-task-definition --task-definition ${TASK_FAMILY} --region ${REGION} --profile deploy)

echo "Creating new Task Definition JSON..."
NEW_TASK_DEF_JSON=$(echo $TASK_DEF_JSON | jq --arg IMAGE "${IMAGE_URI}" '
    .taskDefinition | 
    {
        family: .family,
        taskRoleArn: .taskRoleArn,
        executionRoleArn: .executionRoleArn,
        networkMode: .networkMode,
        containerDefinitions: [.containerDefinitions[] | .image = $IMAGE],
        volumes: .volumes,
        placementConstraints: .placementConstraints,
        requiresCompatibilities: .requiresCompatibilities,
        cpu: .cpu,
        memory: .memory,
        runtimePlatform: .runtimePlatform,
        ephemeralStorage: .ephemeralStorage
    } | del(.runtimePlatform | select(. == null)) | del(.ephemeralStorage | select(. == null))
')

echo "Registering new Task Definition..."
REGISTER_OUTPUT=$(aws ecs register-task-definition --cli-input-json "$NEW_TASK_DEF_JSON" --region ${REGION} --profile deploy)
NEW_TASK_DEF_ARN=$(echo $REGISTER_OUTPUT | jq -r '.taskDefinition.taskDefinitionArn')
echo "Registered: $NEW_TASK_DEF_ARN"

echo "Updating Step Function..."
CURRENT_SFN_DEF=$(aws stepfunctions describe-state-machine --state-machine-arn ${SFN_ARN} --region ${REGION} --profile deploy | jq -r '.definition')

NEW_SFN_DEF=$(echo $CURRENT_SFN_DEF | jq --arg ARN "$NEW_TASK_DEF_ARN" '.States.RunProcessorTask.Parameters.TaskDefinition = $ARN')

aws stepfunctions update-state-machine \
    --state-machine-arn ${SFN_ARN} \
    --definition "$NEW_SFN_DEF" \
    --region ${REGION} \
    --profile deploy

echo "Deployment Complete! State Machine updated to use $NEW_TASK_DEF_ARN with image $IMAGE_URI"
