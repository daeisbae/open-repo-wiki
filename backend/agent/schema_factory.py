from enum import Enum
from typing import Type, Union
from pydantic import BaseModel, Field


class FileSchema(BaseModel):
    usage: str = Field(
        ...,
        description='What the file is used for. Describe less than 10 words (ex. Data Parsing, API Requests, etc.).'
    )
    summary: str = Field(
        ...,
        description=(
                'Summary of the file talking about its main purpose, and its role in the project.\n'
                + 'Include Markdown links to important code blocks within this file using the format\n`'
                + '[{Description of Code Block}]({Full github url of the file including the start line with optional ending line}#L{startLine}-L{endLine})` where applicable.\n'
                + 'Also you should not return more than 2-3 paragraphs of summary.'
        )
    )


class FolderSchema(BaseModel):
    usage: str = Field(
        description='Purpose of the folder (e.g., Server Lifecycle Management, API Utility Functions). Limit to 10 words.'
    )
    summary: str = Field(
        description=(
            'Summary of the folder, its main purpose, and role in the project. '
            'Include Markdown links to important code blocks using the format '
            '`[{Description of Code Block}]({Full GitHub URL}#L{startLine}-L{endLine})`.'
        )
    )

