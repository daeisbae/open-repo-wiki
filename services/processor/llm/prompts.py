"""Prompt templates for LLM summarization.

Ported from src/agent/prompt.py for the AWS serverless architecture.

Requirements: 5.6, 5.7
"""


CODE_PROMPT: str = """
You are an expert software engineer and your task is to deeply analyze a provided codebase from a GitHub repository. Your goal is to generate a comprehensive and structured summary of the codebase that is suitable for a developer-friendly wiki page in markdown format but without backticks.

**Input:**

You will receive the following information, extracted from a GitHub repository:

1. **Repository Description:**
*   'description': (A textual description of the repository, although it may not be available or be correct)
2. **Code File:**
* The raw content of code files within the repository.
* The owner of the repository.
* The repository name.
* The commit sha of the repository.
* The path to the code file within the repository.

**Analysis Tasks:**

1. **High-Level Overview:**
*   Provide a concise summary of the file responsibilities and functionalities based on it's content.
*   Explain its role in the overall system.
*   Identify its dependencies on other modules/components.
*   Highlight any important classes, functions, or data structures.
*   Link all the code blocks (Class,Function,Enum,Exception) that are referenced using the following markdown link format: [`Description of Code Block`](Full github url of the file including the start line with optional ending line#L{startLine}-L{endLine}). This is in the form of "https://github.com/{owner}/{repo}/blob/{commitSha}/{path}#L{lineStart}-L{lineEnd}".
2. **Code-Level Insights:**
*   Analyze the code files to understand the implementation details.
*   Identify core algorithms, data structures, and design patterns used.
*   Provide a summary of how data flows between different parts of the system.
3. **Dependencies and Relationships:**
*   Clearly document the relationships between different modules, classes, and functions.
*   Explain how different parts of the codebase interact with each other.

**Output:**
"""


FOLDER_PROMPT: str = """
You are an expert software engineer and your task is to deeply analyze a provided codebase from a GitHub repository. Your goal is to generate a comprehensive and structured summary of the codebase that is suitable for a developer-friendly wiki page in markdown format but without backticks.

**Input:**

You will receive the following information, summarized from the expert software engineer:

1. **Repository Description:**
*   'description': (A textual description of the repository, although it may not be available or be correct)
2. **Code Files:**
* The summary of code files within the repository.
* The owner of the repository.
* The repository name.
* The commit sha of the repository.
* The path to the code file within the repository.
3. **Import/Dependency Information (if provided):**
* Raw import statements detected in each file to help understand dependencies.

**Analysis Tasks:**

1. **High-Level Overview:**
*   Start by providing the core functionality among the folders or files. (ex. the folder name "core", "src" or folder with the same repository name usually contains the core functionality of the system. You can ignore utility folders unless they contain important information or there are nothing to explain.)
*   Provide a concise summary of the folder's responsibilities and functionalities based on it's sub-files and sub-folders summaries.
*   Explain its role in the overall system.
*   Identify its dependencies on other modules/components/folder.
*   Highlight any important classes, functions, or data structures in it's sub-files and sub-folders.
*   Link all the code blocks that are referenced using the following markdown link format: [`Description of Code Block`](Full github url of the file including the start line with optional ending line#L{startLine}-L{endLine}). This is in the form of "https://github.com/{owner}/{repo}/blob/{commitSha}/{path}#L{lineStart}-L{lineEnd}".

2. **Dependencies and Relationships:**
*   Clearly document the relationships between different folders and files.
*   Explain how different parts of the codebase interact with each other.

3. **Dependency Graph (Mermaid):**
*   Generate a Mermaid flowchart (graph TD) showing file relationships WITHIN this folder.
*   Use SHORT labeled arrows (under 5 words) that describe the relationship/action.
*   Good labels: "provides config to", "transforms data for", "reports errors to", "validates input for", "extends", "implements", "fetches from", "stores in", "parses for", "informs", "uses models from"
*   Only show meaningful relationships between files in this folder.
*   CRITICAL: Use SAFE, alphanumeric identifiers for nodes (no special chars like /, @, -, or spaces). Use the filename as the LABEL.
*   Format: safe_id["Filename"]
*   Example:
    graph TD
        services["services"] -->|uses models from| shared_models["@shared/models"]
        api_client["api-client"] -->|calls| backend_api["backend/api"]
        views -->|delegates to| services
        tasks -->|async wrapper for| services
        config -->|provides settings to| services

**Output:**
"""


FILE_PROMPT_TEMPLATE: str = """The following instruction is given:
{requirements}
{format_instructions}
The given repository owner is {repo_owner} with repository name of {repo_name}
The commit SHA referenced is {commit_sha}
The path of the file is {path}
Below is the code for your task: {code}"""


FOLDER_PROMPT_TEMPLATE: str = """The following instruction is given:
{requirements}
{format_instructions}
The given repository owner is {repo_owner} with repository name of {repo_name}
The commit SHA referenced is {commit_sha}
The path of the folder is {path}
Below are the summaries for the codebase:
{ai_summaries}"""
