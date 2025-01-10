from enum import Enum
from typing import List, Optional
from pydantic import BaseModel
from langchain.prompts import PromptTemplate


class PromptType(str, Enum):
    FOLDER = 'folder'
    FILE = 'file'


class RepoInfo(BaseModel):
    repo_owner: str
    repo_name: str
    commit_sha: str
    path: str


class BasePromptTemplateVariables(RepoInfo):
    requirements: str
    format_instructions: str


class FilePromptTemplateVariables(BasePromptTemplateVariables):
    code: str


class FolderPromptTemplateVariables(BasePromptTemplateVariables):
    ai_summaries: str


class PromptTemplateConfig(BaseModel):
    template: str


class PromptGenerator:
    def __init__(self, config: PromptTemplateConfig, prompt_type: PromptType):
        self.prompt = PromptTemplate.from_template(config.template)
        self.prompt_type = prompt_type

    async def generate(
            self,
            variables: BasePromptTemplateVariables,
            code: Optional[str] = None,
            ai_summaries: Optional[List[str]] = None
    ) -> Optional[str]:
        prompt_map = {
            PromptType.FOLDER: '\n'.join(ai_summaries) if ai_summaries else '',
            PromptType.FILE: code or '',
        }

        user_prompt = prompt_map.get(self.prompt_type, '')
        if not user_prompt:
            return None

        if self.prompt_type == PromptType.FILE:
            full_variables = variables.model_dump()
            full_variables['code'] = user_prompt
        else:
            full_variables = variables.model_dump()
            full_variables['ai_summaries'] = user_prompt

        return self.prompt.format(**full_variables)
