import re
from typing import List, Dict

from github.fetch_repo import RepoTreeResult


def whitelisted_file(files: List[str], regex_filter: List[str]) -> List[str]:
    filter_patterns = [re.compile(pattern) for pattern in regex_filter]
    return [file for file in files if any(pattern.search(file.lower()) for pattern in filter_patterns)]


def blacklisted_files(files: List[str], regex_filter: List[str]) -> List[str]:
    filter_patterns = [re.compile(pattern) for pattern in regex_filter]
    return [file for file in files if not any(pattern.search(file.lower()) for pattern in filter_patterns)]


def blacklisted_folder(folders: List[RepoTreeResult], regex_filter: List[str]) -> List[RepoTreeResult]:
    filter_patterns = [re.compile(pattern) for pattern in regex_filter]
    return [folder for folder in folders if
            not any(pattern.search(folder.path.lower()) for pattern in filter_patterns)]


whitelisted_filter = [
    r'\.py$',
    r'\.js$',
    r'\.ts$',
    r'\.java$',
    r'\.scala$',
    r'README\.md',
    r'\.cpp$',
    r'\.cc$',
    r'\.cxx$',
    r'\.hpp$',
    r'\.hxx$',
    r'\.h$',
    r'\.go$',
    r'\.rb$',
    r'\.rs$',
    r'\.php$',
]

blacklisted_file = [
    r'(^|/)\.[^/]+($|/)',  # File starting with a dot
    r'__\w+',  # __init__.py, __main__.py, etc.
    r'setup',  # setup.py, setup.js
    r'd\.ts',  # *.d.ts
    r'setup',
    r'build',
    r'demo',
    r'entrypoint',
    r'example',
    r'config',
    r'sponsor',  # sponsors.js
    r'contrib',  # contributors.js
    r'gulpfile',
    r'webpack',
    r'\.min\.js',
    r'\.spec',  # *.spec.js, *.spec.ts
    r'types',
]

blacklisted_filter = [
    r'(^|/)\.[^/]+($|/)',  # File starting with a dot
    r'__\w+',  # __pycache__, etc.
    r'appimage',
    r'appearance',
    r'art',
    r'assets',
    r'audio',
    r'bench',
    r'bin',
    r'build',
    r'cache',
    r'changelog',
    r'ci',
    r'cmake',
    r'contrib',
    r'debug',
    r'demo',
    r'developer',
    r'docker',
    r'doc',
    r'e2e',
    r'example',
    r'extra',
    r'esm',
    r'guide',
    r'html',
    r'image',
    r'img',
    r'node_modules',
    r'output',
    r'public',
    r'picture',
    r'release',
    r'requirement',
    r'sample',
    r'script',
    r'setup',
    r'static',
    r'support',
    r'screenshot',
    r'target',
    r'temp',
    r'theme',
    r'tool',
    r'test',
    r'third_party',
    r'tmp',
    r'vendor',
    r'video',
    r'workflows',
    r'locale',
    r'conf',
    r'tutorial',
]
