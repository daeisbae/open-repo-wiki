from typing import Optional, List

from agent.prompt import CodePrompt, FolderPrompt
from agent.schema_parser import SchemaParser
from agent.schema_factory import FileSchema, FolderSchema
from agent.prompt_generator import PromptGenerator, FilePromptTemplateVariables, PromptTemplateConfig, PromptType, \
    RepoInfo, \
    FolderPromptTemplateVariables
from agent.code_splitter import CodeSplitter
from llm.llm_provider import LLMProvider


# Base Processor
class BaseProcessor:
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.schema_parser: Optional[SchemaParser] = None
        self.prompt_generator: Optional[PromptGenerator] = None

    async def process(self, prompt: str) -> dict:
        response = await self.llm.run(prompt)
        return self.schema_parser.parse(response)


# Code Processor
class CodeProcessor(BaseProcessor):
    def __init__(self, llm: LLMProvider):
        super().__init__(llm)
        self.code_splitter = CodeSplitter(200, 25)
        self.schema_parser = SchemaParser(FileSchema)
        self.prompt_generator = PromptGenerator(
            PromptTemplateConfig(
                template=(
                    'The following instruction is given:\n{requirements}\n{format_instructions}\n'
                    'The given repository owner is {repo_owner} with repository name of {repo_name}\n'
                    'The commit SHA referenced is {commit_sha}\n'
                    'The path of the file is {path}\n'
                    'Below is the code for your task: {code}'
                )
            ),
            PromptType.FILE
        )

    async def generate(self, code: str, repo_info: dict[str, str]) -> dict:
        extension = repo_info.get('path').split('.').pop()
        splitted_code = self.code_splitter.split_code(extension, code)
        variables = FilePromptTemplateVariables(
            requirements=CodePrompt,
            format_instructions=self.schema_parser.format_instructions,
            code=splitted_code,
            repo_name=repo_info.get('repo_name'),
            repo_owner=repo_info.get('repo_owner'),
            commit_sha=repo_info.get('commit_sha'),
            path=repo_info.get('path'),
        )
        prompt = await self.prompt_generator.generate(variables, code=variables.code)
        return await self.process(prompt)


# Folder Processor
class FolderProcessor(BaseProcessor):
    def __init__(self, llm: LLMProvider):
        super().__init__(llm)
        self.schema_parser = SchemaParser(FolderSchema)
        self.prompt_generator = PromptGenerator(
            PromptTemplateConfig(
                template=(
                    'The following instruction is given:\n{requirements}\n{format_instructions}\n'
                    'The given repository owner is {repo_owner} with repository name of {repo_name}\n'
                    'The commit SHA referenced is {commit_sha}\n'
                    'The path of the folder is {path}\n'
                    'Below are the summaries for the codebase:\n{ai_summaries}'
                )
            ),
            PromptType.FOLDER
        )

    async def generate(self, ai_summaries: List[str], repo_info: dict[str, str]) -> dict:
        variables = FolderPromptTemplateVariables(
            requirements=FolderPrompt,
            format_instructions=self.schema_parser.format_instructions,
            ai_summaries='\n'.join(ai_summaries),
            repo_owner=repo_info.get('repo_owner'),
            commit_sha=repo_info.get('commit_sha'),
            path=repo_info.get('path'),
            repo_name=repo_info.get('repo_name'),
        )
        prompt = await self.prompt_generator.generate(variables, ai_summaries=ai_summaries)
        return await self.process(prompt)
