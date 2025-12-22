#!/bin/bash
set -e

# Configuration
BUCKET_NAME="openrepowiki-artifacts-prod"
DISTRIBUTION_ID="E35FQGNDF29U1M"
REGION="us-east-1"
PROFILE="deploy"

echo "=== 🚀 Starting Frontend Deployment ==="

# 1. Build
echo "📦 Building frontend..."
cd frontend
npm run build
cd ..

# 2. Sync Assets (long cache)
# We sync assets folder first. These have hash in filename so we want them cached forever.
echo "🔄 Syncing assets to S3 (Cache: 1 year)..."
AWS_PROFILE=$PROFILE aws s3 sync frontend/dist/assets/ s3://$BUCKET_NAME/frontend/assets/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --region $REGION

# 3. Upload index.html (no cache)
# This is critical. We want browsers to ALWAYS check for new version of index.html
echo "📄 Uploading index.html (Cache: no-cache)..."
AWS_PROFILE=$PROFILE aws s3 cp frontend/dist/index.html s3://$BUCKET_NAME/frontend/index.html \
  --cache-control "no-cache, no-store, must-revalidate" \
  --content-type "text/html" \
  --region $REGION

# 4. Upload other root files (vite.svg etc)
echo "📂 Uploading other root files..."
AWS_PROFILE=$PROFILE aws s3 cp frontend/dist/vite.svg s3://$BUCKET_NAME/frontend/vite.svg \
  --region $REGION

# 5. Invalidate CloudFront
echo "🧹 Invalidating CloudFront cache..."
INVALIDATION_ID=$(AWS_PROFILE=$PROFILE aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*" \
  --query 'Invalidation.Id' \
  --output text \
  --region $REGION)

echo "✅ Deployment Complete!"
echo "Invalidation ID: $INVALIDATION_ID"
echo "URLs:"
echo "  - https://openrepowiki.xyz/"
echo "  - https://openrepowiki.xyz/index.html"
