CREATE TABLE Repository (
    url VARCHAR(255) PRIMARY KEY,
    owner VARCHAR(50) NOT NULL,
    repo VARCHAR(50) NOT NULL,
    language VARCHAR(20) NOT NULL,
    descriptions TEXT,
    default_branch VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Topics (
    topic_name VARCHAR(50) PRIMARY KEY
);

CREATE TABLE RepositoryTopics (
    repository_url VARCHAR(255),
    topic_name VARCHAR(50),
    PRIMARY KEY (repository_url, topic_name),
    FOREIGN KEY (repository_url) REFERENCES Repository(url),
    FOREIGN KEY (topic_name) REFERENCES Topics(topic_name)
);


/**
Last Commit SHA length: https://stackoverflow.com/questions/18134627/how-much-of-a-git-sha-is-generally-considered-necessary-to-uniquely-identify-a
*/
CREATE TABLE Branch (
    last_commit_sha VARCHAR(40) NOT NULL PRIMARY KEY,
    name            VARCHAR(50) NOT NULL,
    repository_url  VARCHAR(255),
    commit_at       TIMESTAMP,
    CONSTRAINT fk_repository FOREIGN KEY (repository_url) REFERENCES Repository(url)
);

CREATE TABLE Folder (
    folder_id SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    path VARCHAR(100),
    parent_folder_id SERIAL,
    branch_sha VARCHAR(40) NOT NULL,
    branch_name VARCHAR(50) NOT NULL,
    FOREIGN KEY (parent_folder_id) REFERENCES Folder(folder_id),
    FOREIGN KEY (branch_sha) REFERENCES Branch(last_commit_sha),
    FOREIGN KEY (branch_name) REFERENCES Branch(name)
);

CREATE TABLE File (
    file_id SERIAL PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    sha VARCHAR(40) NOT NULL,
    language VARCHAR(20),
    parent_folder_id SERIAL NOT NULL,
    ai_summary TEXT,
    FOREIGN KEY (parent_folder_id) REFERENCES Folder(folder_id)
);