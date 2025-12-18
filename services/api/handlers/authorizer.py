"""
Lambda Authorizer for API Gateway.

Validates HMAC-SHA256 signed requests to prevent unauthorized API access.
Only requests with valid signatures from the frontend will be allowed.

Headers required:
- X-Timestamp: Unix timestamp (must be within 5 minutes)
- X-Signature: HMAC-SHA256 signature of "{timestamp}:{method}:{path}"
"""

import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(os.environ.get('LOG_LEVEL', 'INFO'))

# Cache the signing key to avoid fetching from Secrets Manager on every request
_cached_signing_key: str | None = None


def get_signing_key() -> str:
    """Retrieve signing key from AWS Secrets Manager with caching."""
    global _cached_signing_key
    
    if _cached_signing_key is not None:
        return _cached_signing_key
    
    secret_arn = os.environ.get('SIGNING_SECRET_ARN')
    if not secret_arn:
        # Fallback to environment variable for local testing
        key = os.environ.get('SIGNING_KEY')
        if key:
            return key
        raise ValueError("SIGNING_SECRET_ARN or SIGNING_KEY environment variable required")
    
    client = boto3.client('secretsmanager')
    try:
        response = client.get_secret_value(SecretId=secret_arn)
        secret_value = response.get('SecretString')
        
        # Try to parse as JSON first (in case it's a key-value pair)
        try:
            secret_data = json.loads(secret_value)
            _cached_signing_key = secret_data.get('signing_key', secret_value)
        except json.JSONDecodeError:
            _cached_signing_key = secret_value
        
        return _cached_signing_key
    except ClientError as e:
        logger.error(f"Failed to retrieve signing key: {e}")
        raise


def generate_policy(principal_id: str, effect: str, resource: str, context: dict | None = None) -> dict[str, Any]:
    """
    Generate an IAM policy document for API Gateway.
    
    Args:
        principal_id: Identifier for the principal (user/caller)
        effect: 'Allow' or 'Deny'
        resource: The API Gateway method ARN
        context: Optional context to pass to the backend
    
    Returns:
        IAM policy document
    """
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }
    
    if context:
        policy['context'] = context
    
    return policy


def verify_signature(timestamp: str, method: str, path: str, signature: str) -> bool:
    """
    Verify HMAC-SHA256 signature.
    
    Args:
        timestamp: Unix timestamp string
        method: HTTP method (GET, POST, etc.)
        path: Request path (e.g., /jobs)
        signature: Hex-encoded HMAC-SHA256 signature
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        signing_key = get_signing_key()
        message = f"{timestamp}:{method}:{path}"
        
        expected_signature = hmac.new(
            signing_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature.lower(), expected_signature.lower())
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda authorizer handler.
    
    Validates:
    1. X-Timestamp header is present and within 5 minutes
    2. X-Signature header is present and valid
    
    Args:
        event: API Gateway authorizer event
        context: Lambda context
    
    Returns:
        IAM policy document (Allow or Deny)
    """
    logger.info(f"Authorizer invoked: {json.dumps({k: v for k, v in event.items() if k != 'headers'})}")
    
    # Get the method ARN for the policy
    method_arn = event.get('methodArn', '*')
    
    # For REQUEST type authorizers, headers are in the headers field
    headers = event.get('headers', {})
    
    # Normalize header keys to lowercase
    headers_lower = {k.lower(): v for k, v in headers.items()} if headers else {}
    
    # Extract required headers
    timestamp = headers_lower.get('x-timestamp')
    signature = headers_lower.get('x-signature')
    
    # Log for debugging (without sensitive data)
    logger.info(f"Headers present - timestamp: {bool(timestamp)}, signature: {bool(signature)}")
    
    # Validate headers are present
    if not timestamp or not signature:
        logger.warning("Missing required headers (X-Timestamp or X-Signature)")
        return generate_policy('unauthorized', 'Deny', method_arn)
    
    # Validate timestamp is within 5 minutes (300 seconds)
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        time_diff = abs(current_time - request_time)
        
        if time_diff > 300:
            logger.warning(f"Timestamp too old or in future: {time_diff} seconds difference")
            return generate_policy('unauthorized', 'Deny', method_arn)
    except ValueError:
        logger.warning(f"Invalid timestamp format: {timestamp}")
        return generate_policy('unauthorized', 'Deny', method_arn)
    
    # Extract HTTP method and path from event
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('httpMethod', 'POST')
    path = event.get('path') or event.get('requestContext', {}).get('path', '/jobs')
    
    # Verify signature
    if not verify_signature(timestamp, http_method, path, signature):
        logger.warning("Invalid signature")
        return generate_policy('unauthorized', 'Deny', method_arn)
    
    # Signature is valid - allow the request
    logger.info("Request authorized successfully")
    return generate_policy(
        'authorized-user',
        'Allow',
        method_arn,
        {'timestamp': timestamp}
    )
