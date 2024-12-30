
# OpenRepoWiki

[OpenRepoWiki Example Image](https://github.com/daeisbae/open-repo-wiki/blob/main/assets/openrepowiki.png)

**OpenRepoWiki** is a tool that automatically generates a comprehensive wiki page for any given GitHub repository. It leverages an LLM enhanced with prompt engineering to analyze the repository's codebase, structure, and documentation, providing users with a clear and concise understanding of the project.

## Features

- **Automated Wiki Generation:** Creates a summarized overview of a repository's purpose, functionality, and core components.
- **Codebase Analysis:** Analyzes the code structure, identifies key files and functions, and explains their roles within the project.

## Installation

### Requirements

- Either Google AI Studio or Deepseek API Key
- PostgreSQL (For storing the summarized repository information)
- Github API Key (To get more quota requesting the repository data)

### Configuration

1. Copy .env.example to .env
2. Configure all the variables given (Follow the instructions)
3. Install all the dependencies (`npm install`)
4. Run the server (`npm run dev`)

## Requirements and Documentation

Refer [Documentation](https://github.com/daeisbae/open-repo-wiki/blob/main/docs/)
