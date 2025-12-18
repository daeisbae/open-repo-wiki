"""Lambda handler entry point for API Gateway.

This module provides the main entry points for AWS Lambda functions
that handle API Gateway requests. It routes requests to the appropriate
handler based on the HTTP method and resource path.

Lambda Handler Entry Points:
- jobs_handler: Handles POST /jobs and GET /jobs/{jobId}
- repos_handler: Handles GET /repos/{repoId}/tree and GET /repos/{repoId}/page

Requirements: Phase 3 infrastructure
"""

from typing import Any

from services.api.handlers.jobs import create_job, get_job
from services.api.handlers.repos import get_tree, get_page


def jobs_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for Jobs API endpoints.
    
    Routes:
        POST /jobs -> create_job
        GET /jobs/{jobId} -> get_job
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response dict
    """
    http_method = event.get("httpMethod", "").upper()
    
    if http_method == "POST":
        return create_job(event, context)
    elif http_method == "GET":
        return get_job(event, context)
    elif http_method == "OPTIONS":
        # Handle CORS preflight
        return _cors_response()
    else:
        return _method_not_allowed(http_method)


def repos_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler for Repos API endpoints.
    
    Routes:
        GET /repos/{repoId}/tree -> get_tree
        GET /repos/{repoId}/page -> get_page
    
    Args:
        event: API Gateway event
        context: Lambda context
        
    Returns:
        API Gateway response dict
    """
    http_method = event.get("httpMethod", "").upper()
    resource = event.get("resource", "")
    
    if http_method == "OPTIONS":
        return _cors_response()
    
    if http_method != "GET":
        return _method_not_allowed(http_method)
    
    # Route based on resource path
    if "/tree" in resource:
        return get_tree(event, context)
    elif "/page" in resource:
        return get_page(event, context)
    else:
        return _not_found(resource)


def _cors_response() -> dict[str, Any]:
    """Return CORS preflight response."""
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": "",
    }


def _method_not_allowed(method: str) -> dict[str, Any]:
    """Return 405 Method Not Allowed response."""
    import json
    return {
        "statusCode": 405,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": f"Method '{method}' not allowed",
            }
        }),
    }


def _not_found(resource: str) -> dict[str, Any]:
    """Return 404 Not Found response."""
    import json
    return {
        "statusCode": 404,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Resource '{resource}' not found",
            }
        }),
    }
