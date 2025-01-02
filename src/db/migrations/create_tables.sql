CREATE TABLE IF NOT EXISTS Repository (
    url             VARCHAR(255) PRIMARY KEY,
    owner           VARCHAR(50) NOT NULL,
    repo            VARCHAR(50) NOT NULL,
    language        VARCHAR(20) NOT NULL,
    descriptions    TEXT,
    default_branch  VARCHAR(50),
    stars           INT,
    forks           INT
);

CREATE TABLE IF NOT EXISTS Topics (
    topic_name      VARCHAR(50) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS RepositoryTopics (
    repository_url  VARCHAR(255),
    topic_name      VARCHAR(50),
    PRIMARY KEY (repository_url, topic_name),
    FOREIGN KEY (repository_url) REFERENCES Repository(url) ON DELETE CASCADE,
    FOREIGN KEY (topic_name) REFERENCES Topics(topic_name)
);

/**
Last Commit SHA length: https://stackoverflow.com/questions/18134627/how-much-of-a-git-sha-is-generally-considered-necessary-to-uniquely-identify-a
*/
CREATE TABLE IF NOT EXISTS Branch (
    branch_id       SERIAL PRIMARY KEY,
    last_commit_sha VARCHAR(40) NOT NULL,
    name            VARCHAR(50) NOT NULL,
    repository_url  VARCHAR(255),
    commit_at       TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ai_summary      TEXT,
    FOREIGN KEY (repository_url) REFERENCES Repository(url) ON DELETE CASCADE,
    CONSTRAINT unique_last_commit_per_repo UNIQUE (repository_url, last_commit_sha)
);

CREATE TABLE IF NOT EXISTS Folder (
    folder_id           SERIAL PRIMARY KEY,
    name                VARCHAR(30),
    path                VARCHAR(150) NOT NULL,
    usage               VARCHAR(100),
    parent_folder_id    INTEGER,
    ai_summary          TEXT,
    branch_id           INTEGER NOT NULL,
    FOREIGN KEY (parent_folder_id) REFERENCES Folder(folder_id) ON DELETE CASCADE,
    FOREIGN KEY (branch_id) REFERENCES Branch(branch_id) ON DELETE CASCADE,
    CHECK ( (path = '' AND parent_folder_id IS NULL) OR (path != '' AND parent_folder_id IS NOT NULL) )
);

CREATE TABLE IF NOT EXISTS File (
    file_id         SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    language        VARCHAR(20),
    folder_id       INTEGER NOT NULL,
    content         TEXT,
    ai_summary      TEXT,
    usage           VARCHAR(100),
    FOREIGN KEY (folder_id) REFERENCES Folder(folder_id) ON DELETE CASCADE
);