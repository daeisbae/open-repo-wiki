from langchain.output_parsers import PydanticOutputParser
from typing import Union, Type
import re
import asyncio

from pydantic import BaseModel

from agent.schema_factory import FolderSchema, FileSchema


class SchemaParser:
    def __init__(self, schema: Type[BaseModel]):
        self.output_parser = PydanticOutputParser(pydantic_object=schema)
        self.format_instructions = self.output_parser.get_format_instructions()

    def parse(self, output: str) -> Union[FileSchema, FolderSchema]:
        filtered_output = self.remove_json_markdown_wrapper(output)
        return self.output_parser.parse(filtered_output)

    def remove_json_markdown_wrapper(self, llm_output: str) -> str:
        match = re.search(r'\{.*\}', llm_output, re.DOTALL)
        if match:
            return match.group(0)
        return llm_output.strip()