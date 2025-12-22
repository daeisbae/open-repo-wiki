#!/bin/bash
# Build Lambda deployment package for API handlers
#
# This script creates a deployment package containing:
# - Lambda handler code (services/api/)
# - Shared libraries (shared/)
# - Python dependencies from requirements.txt
#
# Usage: ./build_package.sh [output_dir]
#
# Requirements: Phase 3 infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="${1:-$SCRIPT_DIR/dist}"
PACKAGE_NAME="api-lambda-package.zip"

echo "Building Lambda deployment package..."
echo "Project root: $PROJECT_ROOT"
echo "Output directory: $OUTPUT_DIR"

# Create clean output directory
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Create temporary build directory
BUILD_DIR=$(mktemp -d)
trap "rm -rf $BUILD_DIR" EXIT

echo "Installing dependencies (forcing x86_64 Linux)..."
pip install -r "$SCRIPT_DIR/requirements.txt" \
    -t "$BUILD_DIR" \
    --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.11 \
    --only-binary=:all: \
    --upgrade \
    --quiet

echo "Copying application code..."
# Copy shared libraries
cp -r "$PROJECT_ROOT/shared" "$BUILD_DIR/"

# Copy services/api module
mkdir -p "$BUILD_DIR/services/api"
cp -r "$SCRIPT_DIR/"*.py "$BUILD_DIR/services/api/"
cp -r "$SCRIPT_DIR/handlers" "$BUILD_DIR/services/api/"

# Create services/__init__.py if it doesn't exist
mkdir -p "$BUILD_DIR/services"
echo '"""Services package for Lambda handlers."""' > "$BUILD_DIR/services/__init__.py"

echo "Creating deployment package..."
cd "$BUILD_DIR"
zip -r "$OUTPUT_DIR/$PACKAGE_NAME" . -x "*.pyc" -x "__pycache__/*" -x "*.dist-info/*" --quiet

echo "Package created: $OUTPUT_DIR/$PACKAGE_NAME"
echo "Package size: $(du -h "$OUTPUT_DIR/$PACKAGE_NAME" | cut -f1)"

echo "Done!"
