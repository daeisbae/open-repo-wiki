
# OpenRepoWiki

![OpenRepoWiki Example Image](https://github.com/daeisbae/open-repo-wiki/blob/main/assets/openrepowiki.png)

**OpenRepoWiki** is a tool that automatically generates a comprehensive wiki page for any given GitHub repository. I **hate** reading code, but I want to learn how to build stuffs from websites to databases. That's why I built **OpenRepoWiki**, where we can understand the purpose of that files and folders of a particular repository.

## Features

- **Automated Wiki Generation:** Creates a summarized overview of a repository's purpose, functionality, and core components.
- **Codebase Analysis:** Analyzes the code structure, identifies key files and functions, and explains their roles within the project.
- **Link To That Code Block:** The sky-blue highlighted code block will point to the Github link where it referenced.

## Installation

### Requirements

- Either Google AI Studio or Deepseek API Key
- PostgreSQL (For storing the summarized repository information)
- Github API Key (To get more quota requesting the repository data)
- Amazon S3 (You can ignore the parameters if you are going to use it locally. You need to use certificate for your Database if you are going to host it.)
- Docker (If you are hosting locally)

### Configuration (Local)

1. Copy `.env.example` to `.env`
2. Configure all the variables given in `.env`
3. Run `docker compose up` or `docker compose up -d` to hide the output

### Configuration (Cloud)

1. Create PostgreSQL instance
2. Copy `.env.example` to `.env`
3. Configure all the variables given in `.env`
4. Install all the dependencies (`npm install`)
5. Initialize the database by typing (`npm run db:init`). If this does not work, you can install [database manager GUI](https://github.com/beekeeper-studio/beekeeper-studio), connect to the database then manually execute SQL [src/db/migrations/create_tables.sql](https://github.com/daeisbae/open-repo-wiki/blob/main/src/db/migrations/create_tables.sql)
6. Build the server (`npm run build`)
7. Run (`npm start`)


#### Ollama Configuration Guide

- It's recommended if you can run bigger LLM than 14b parameter.
- You do not need to provide the API KEY
- Set LLM_PROVIDER to Ollama (It is going to connect to default ollama endpoint)
- Set LLM_MODELNAME to the model name you can see from Ollama using the command `ollama ls`
- It is recommended to set TOKEN_PROCESSING_CHARACTER_LIMIT between 10000-20000 (Approx 300-600 lines of code) if you are using low param LLM (ex. 8b, 14b)

**Example:**

```
LLM_PROVIDER=ollama
LLM_APIKEY=
LLM_MODELNAME=qwen2.5:14b
```

### Additional Information

> [!CAUTION]
> Before using this, it can easily use 1 million input / output tokens per Repository. Hence it is recommended to use cheaper LLM.

- If you are going to host it locally, you will only need to configure the Docker PostgreSQL container, Github API Key, and Google AI Studio or Deepseek API Key

## Requirements and Documentation

Refer [Documentation](https://github.com/daeisbae/open-repo-wiki/blob/main/docs/)
