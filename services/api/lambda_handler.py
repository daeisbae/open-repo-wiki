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
import json
import os
import traceback

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
    print(f"DEBUG_JOBS_HANDLER Event: {json.dumps(event)}")
    
    try:
        if http_method == "POST":
            response = create_job(event, context)
            print(f"DEBUG_JOBS_HANDLER Response: {json.dumps(response)}")
            return response
        elif http_method == "GET":
            response = get_job(event, context)
            print(f"DEBUG_JOBS_HANDLER Response: {json.dumps(response)}")
            return response
        elif http_method == "OPTIONS":
            # Handle CORS preflight
            return _cors_response()
        else:
            return _method_not_allowed(http_method)
    except Exception as e:
        print(f"Unhandled error in jobs_handler: {e}")
        import traceback
        traceback.print_exc()
        return _server_error(e)


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
    print(f"DEBUG_REPOS_HANDLER Event: {json.dumps(event)}")
    
    try:
        if http_method == "OPTIONS":
            return _cors_response()
        
        if http_method != "GET":
            return _method_not_allowed(http_method)
        
        # Route based on resource path
        if "/tree" in resource:
            response = get_tree(event, context)
            print(f"DEBUG_REPOS_HANDLER Response: {str(response)}")
            return response
        elif "/page" in resource:
            response = get_page(event, context)
            print(f"DEBUG_REPOS_HANDLER Response: {json.dumps(response)}")
            return response
        else:
            return _not_found(resource)
    except Exception as e:
        print(f"Unhandled error in repos_handler: {e}")
        import traceback
        traceback.print_exc()
        return _server_error(e)


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
        "isBase64Encoded": False,
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
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps({
            "error": {
                "code": "NOT_FOUND",
                "message": f"Resource '{resource}' not found",
            }
        }),
        "isBase64Encoded": False,
    }


def _server_error(error: Exception) -> dict[str, Any]:
    """Return 500 Internal Server Error response."""
    import json
    
    # In production, we might want to mask the internal error details
    # But for debugging, it's very helpful to see them
    error_msg = str(error)
    
    return {
        "statusCode": 500,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps({
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": error_msg,
            }
        }),
        "isBase64Encoded": False,
    }
