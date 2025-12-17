"""Output schemas for LLM responses.

Ported from src/agent/schema_factory.py for the AWS serverless architecture.

Requirements: 5.6, 5.7
"""

import json
import re
from typing import Type, TypeVar, Union

from pydantic import BaseModel, Field


class FileSchema(BaseModel):
    """Schema for file summary output from LLM.
    
    Attributes:
        usage: Brief description of what the file is used for.
        summary: Detailed summary of the file's purpose and role.
    """
    usage: str = Field(
        ...,
        description=(
            "What the file is used for. Describe in less than 10 words "
            "(e.g., Data Parsing, API Requests, etc.)."
        ),
    )
    summary: str = Field(
        ...,
        description=(
            "Summary of the file talking about its main purpose and role in the project. "
            "Include Markdown links to important code blocks within this file using the format "
            "`[{Description of Code Block}]({Full GitHub URL}#L{startLine}-L{endLine})` where applicable. "
            "Should not exceed 2-3 paragraphs."
        ),
    )


class FolderSchema(BaseModel):
    """Schema for folder summary output from LLM.
    
    Attributes:
        usage: Brief description of the folder's purpose.
        summary: Detailed summary of the folder's contents and role.
        dependency_graph: Mermaid flowchart showing file relationships.
    """
    usage: str = Field(
        ...,
        description=(
            "Purpose of the folder (e.g., Server Lifecycle Management, API Utility Functions). "
            "Limit to 10 words."
        ),
    )
    summary: str = Field(
        ...,
        description=(
            "Summary of the folder, its main purpose, and role in the project. "
            "Include Markdown links to important code blocks using the format "
            "`[{Description of Code Block}]({Full GitHub URL}#L{startLine}-L{endLine})`."
        ),
    )
    dependency_graph: str = Field(
        default="",
        description=(
            "A Mermaid flowchart (graph TD) showing how files in this folder relate to each other. "
            "Use SHORT labeled arrows (under 5 words) describing the relationship: "
            "e.g., A -->|provides config to| B, C -->|transforms data for| D. "
            "Labels should describe the action/relationship like: uses, informs, transforms, validates, "
            "extends, implements, configures, reports to, fetches from, stores in, parses for, etc. "
            "Only include files with actual relationships. Return empty string if none exist. "
            "Do not include ```mermaid``` fences."
        ),
    )


T = TypeVar("T", bound=BaseModel)


class SchemaParser:
    """Parser for LLM output into structured schemas.
    
    Handles parsing of JSON output from LLM responses, including
    extraction from markdown code blocks.
    """

    def __init__(self, schema: Type[T]):
        """Initialize the schema parser.
        
        Args:
            schema: Pydantic model class to parse into.
        """
        self.schema = schema
        self.format_instructions = self._generate_format_instructions()

    def _generate_format_instructions(self) -> str:
        """Generate format instructions for the LLM.
        
        Returns:
            String with JSON schema and formatting instructions.
        """
        schema_dict = self.schema.model_json_schema()
        properties = schema_dict.get("properties", {})
        required = schema_dict.get("required", [])
        
        fields_desc = []
        for name, prop in properties.items():
            desc = prop.get("description", "No description")
            req = "(required)" if name in required else "(optional)"
            fields_desc.append(f'  "{name}": {req} {desc}')
        
        return (
            "The output should be formatted as a JSON instance that conforms to the JSON schema below.\n\n"
            "As an example, for the schema {\"properties\": {\"foo\": {\"title\": \"Foo\", \"description\": \"a list of strings\", \"type\": \"array\", \"items\": {\"type\": \"string\"}}}, \"required\": [\"foo\"]}\n"
            "the object {\"foo\": [\"bar\", \"baz\"]} is a well-formatted instance of the schema.\n\n"
            "Here is the output schema:\n"
            "```\n"
            "{\n"
            + ",\n".join(fields_desc)
            + "\n}\n"
            "```"
        )

    def parse(self, output: str) -> T:
        """Parse LLM output into the schema.
        
        Args:
            output: Raw LLM output string.
            
        Returns:
            Parsed schema instance.
            
        Raises:
            ValueError: If parsing fails.
        """
        filtered_output = self._extract_json(output)
        try:
            data = json.loads(filtered_output)
            return self.schema.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse LLM output: {e}") from e

    def _extract_json(self, llm_output: str) -> str:
        """Extract JSON from LLM output.
        
        Handles cases where JSON is wrapped in markdown code blocks.
        
        Args:
            llm_output: Raw LLM output.
            
        Returns:
            Extracted JSON string.
        """
        # Try to find JSON object in the output
        match = re.search(r"\{.*\}", llm_output, re.DOTALL)
        if match:
            return match.group(0)
        return llm_output.strip()
