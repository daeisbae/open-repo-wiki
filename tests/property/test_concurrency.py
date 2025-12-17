"""Property-based tests for concurrency limit enforcement.

**Feature: aws-migration, Property 6: Concurrency Limit Enforcement**
**Validates: Requirements 10.1, 10.2**

Tests that:
- For any job submission request, if the count of jobs with status RUNNING
  is >= 10, the API SHALL reject the request with an appropriate error response.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st

from services.api.handlers.jobs import (
    create_job,
    _check_concurrency_limit,
    MAX_CONCURRENT_JOBS,
    APIError,
)
from shared.storage.dynamodb import DynamoDBClient


# =============================================================================
# Strategies for generating test data
# =============================================================================

# Valid GitHub owner names (1-39 chars, alphanumeric with hyphens/underscores/dots)
owner_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"),
    min_size=1,
    max_size=39,
).filter(lambda s: s[0].isalnum())

# Valid GitHub repo names (1-100 chars, alphanumeric with hyphens/underscores/dots)
repo_strategy = st.text(
    alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-"),
    min_size=1,
    max_size=100,
).filter(lambda s: s[0].isalnum())

# Running job count strategy - values at or above the limit
running_jobs_at_limit = st.integers(min_value=MAX_CONCURRENT_JOBS, max_value=1000)

# Running job count strategy - values below the limit
running_jobs_below_limit = st.integers(min_value=0, max_value=MAX_CONCURRENT_JOBS - 1)


# =============================================================================
# Property Tests
# =============================================================================

class TestConcurrencyLimitEnforcement:
    """
    **Feature: aws-migration, Property 6: Concurrency Limit Enforcement**
    **Validates: Requirements 10.1, 10.2**
    
    Property: For any job submission request, if the count of jobs with status
    RUNNING is >= 10, the API SHALL reject the request with an appropriate
    error response.
    """

    @given(running_count=running_jobs_at_limit)
    @settings(max_examples=100, deadline=5000)
    def test_rejects_when_at_or_above_limit(self, running_count: int):
        """
        **Feature: aws-migration, Property 6: Concurrency Limit Enforcement**
        **Validates: Requirements 10.1, 10.2**
        
        For any running job count >= MAX_CONCURRENT_JOBS, the concurrency check
        SHALL raise an APIError with CONCURRENCY_LIMIT code.
        """
        # Create a mock DynamoDB client that returns the running count
        mock_client = MagicMock(spec=DynamoDBClient)
        mock_client.count_running_jobs.return_value = running_count
        
        # The check should raise APIError
        with pytest.raises(APIError) as exc_info:
            _check_concurrency_limit(mock_client)
        
        # Verify error details
        assert exc_info.value.code == "CONCURRENCY_LIMIT"
        assert exc_info.value.status_code == 429
        assert str(MAX_CONCURRENT_JOBS) in exc_info.value.message

    @given(running_count=running_jobs_below_limit)
    @settings(max_examples=100, deadline=5000)
    def test_allows_when_below_limit(self, running_count: int):
        """
        **Feature: aws-migration, Property 6: Concurrency Limit Enforcement**
        **Validates: Requirements 10.1, 10.2**
        
        For any running job count < MAX_CONCURRENT_JOBS, the concurrency check
        SHALL NOT raise an error.
        """
        # Create a mock DynamoDB client that returns the running count
        mock_client = MagicMock(spec=DynamoDBClient)
        mock_client.count_running_jobs.return_value = running_count
        
        # The check should NOT raise an error
        _check_concurrency_limit(mock_client)  # Should complete without exception

    @given(
        owner=owner_strategy,
        repo=repo_strategy,
        running_count=running_jobs_at_limit,
    )
    @settings(max_examples=100, deadline=5000)
    def test_create_job_rejects_at_limit(self, owner: str, repo: str, running_count: int):
        """
        **Feature: aws-migration, Property 6: Concurrency Limit Enforcement**
        **Validates: Requirements 10.1, 10.2**
        
        For any valid owner/repo combination, if running jobs >= limit,
        create_job SHALL return 429 with CONCURRENCY_LIMIT error.
        """
        # Mock the DynamoDB client
        mock_ddb = MagicMock(spec=DynamoDBClient)
        mock_ddb.count_running_jobs.return_value = running_count
        
        event = {
            "body": json.dumps({"owner": owner, "repo": repo}),
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            response = create_job(event, None)
        
        # Should return 429 error
        assert response["statusCode"] == 429
        body = json.loads(response["body"])
        assert body["error"]["code"] == "CONCURRENCY_LIMIT"

    @given(
        owner=owner_strategy,
        repo=repo_strategy,
        running_count=running_jobs_below_limit,
    )
    @settings(max_examples=100, deadline=5000)
    def test_create_job_allows_below_limit(self, owner: str, repo: str, running_count: int):
        """
        **Feature: aws-migration, Property 6: Concurrency Limit Enforcement**
        **Validates: Requirements 10.1, 10.2**
        
        For any valid owner/repo combination, if running jobs < limit,
        create_job SHALL proceed (return 201 or other non-429 status).
        """
        # Mock the DynamoDB client
        mock_ddb = MagicMock(spec=DynamoDBClient)
        mock_ddb.count_running_jobs.return_value = running_count
        mock_ddb.create_job.return_value = None
        
        # Mock the Step Functions client
        mock_sfn = MagicMock()
        mock_sfn.start_execution.return_value = {}
        
        event = {
            "body": json.dumps({"owner": owner, "repo": repo}),
        }
        
        with patch("services.api.handlers.jobs._get_dynamodb_client", return_value=mock_ddb):
            with patch("services.api.handlers.jobs._get_sfn_client", return_value=mock_sfn):
                with patch.dict(os.environ, {"STATE_MACHINE_ARN": "arn:aws:states:us-east-1:123456789:stateMachine:test"}):
                    response = create_job(event, None)
        
        # Should NOT return 429 (concurrency limit)
        assert response["statusCode"] != 429
        # Should return 201 (created) for valid input
        assert response["statusCode"] == 201
        body = json.loads(response["body"])
        assert "jobId" in body
