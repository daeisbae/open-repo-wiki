"""
Dependency Parser - Extracts import statements from various programming languages using regex.
Provides import information to help LLM understand file dependencies.
"""

import re
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ImportInfo:
    """Represents a parsed import statement."""
    module: str  # The imported module/package name
    alias: Optional[str] = None  # Optional alias (as X)
    members: List[str] = field(default_factory=list)  # Specific imports from module
    is_relative: bool = False  # Whether it's a relative import
    raw_statement: str = ""  # The original import statement


class DependencyParser:
    """
    Parses import/require statements from source code files.
    Supports Python, JavaScript/TypeScript, Go, Java, Rust, C/C++, and more.
    """

    # Python import patterns
    PYTHON_IMPORT = re.compile(
        r'^(?:from\s+([\w.]+)\s+)?import\s+(.+?)(?:\s+as\s+(\w+))?$',
        re.MULTILINE
    )
    PYTHON_FROM_IMPORT = re.compile(
        r'^from\s+(\.*)?([\w.]*)\s+import\s+(.+)$',
        re.MULTILINE
    )

    # JavaScript/TypeScript import patterns
    JS_IMPORT_DEFAULT = re.compile(
        r'^import\s+(\w+)\s+from\s+[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )
    JS_IMPORT_NAMED = re.compile(
        r'^import\s+\{([^}]+)\}\s+from\s+[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )
    JS_IMPORT_ALL = re.compile(
        r'^import\s+\*\s+as\s+(\w+)\s+from\s+[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )
    JS_IMPORT_SIDE_EFFECT = re.compile(
        r'^import\s+[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )
    JS_REQUIRE = re.compile(
        r'(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*[\'"]([^"\']+)[\'"]\s*\)',
        re.MULTILINE
    )
    JS_DYNAMIC_IMPORT = re.compile(
        r'import\s*\(\s*[\'"]([^"\']+)[\'"]\s*\)',
        re.MULTILINE
    )

    # Go import patterns
    GO_IMPORT_SINGLE = re.compile(
        r'^import\s+(?:(\w+)\s+)?[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )
    GO_IMPORT_BLOCK = re.compile(
        r'import\s*\(([\s\S]*?)\)',
        re.MULTILINE
    )
    GO_IMPORT_LINE = re.compile(
        r'^\s*(?:(\w+)\s+)?[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Java import patterns
    JAVA_IMPORT = re.compile(
        r'^import\s+(?:static\s+)?([\w.]+(?:\.\*)?)\s*;',
        re.MULTILINE
    )

    # Rust import patterns
    RUST_USE = re.compile(
        r'^use\s+([\w:]+(?:::\{[^}]+\})?(?:::\*)?)\s*;',
        re.MULTILINE
    )

    # C/C++ include patterns
    C_INCLUDE = re.compile(
        r'^#include\s+[<"]([^>"]+)[>"]',
        re.MULTILINE
    )

    # Ruby require patterns
    RUBY_REQUIRE = re.compile(
        r'^(?:require|require_relative)\s+[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # PHP use/require patterns
    PHP_USE = re.compile(
        r'^use\s+([\w\\\\]+)(?:\s+as\s+(\w+))?\s*;',
        re.MULTILINE
    )
    PHP_REQUIRE = re.compile(
        r'(?:require|require_once|include|include_once)\s*\(?\s*[\'"]([^"\']+)[\'"]\s*\)?',
        re.MULTILINE
    )

    # Extension to language mapping
    EXTENSION_MAP = {
        '.py': 'python',
        '.pyw': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
        '.go': 'go',
        '.java': 'java',
        '.rs': 'rust',
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.hpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.rb': 'ruby',
        '.php': 'php',
    }

    def __init__(self):
        self.parsers = {
            'python': self._parse_python,
            'javascript': self._parse_javascript,
            'typescript': self._parse_javascript,  # TS uses same syntax
            'go': self._parse_go,
            'java': self._parse_java,
            'rust': self._parse_rust,
            'c': self._parse_c,
            'cpp': self._parse_c,  # Same syntax
            'ruby': self._parse_ruby,
            'php': self._parse_php,
        }

    def get_language(self, file_path: str) -> Optional[str]:
        """Determine language from file extension."""
        for ext, lang in self.EXTENSION_MAP.items():
            if file_path.endswith(ext):
                return lang
        return None

    def parse(self, content: str, file_path: str) -> List[str]:
        """
        Parse imports from file content.
        Returns a list of imported module names.
        """
        language = self.get_language(file_path)
        if not language or language not in self.parsers:
            return []

        try:
            imports = self.parsers[language](content)
            # Extract just module names for storage
            return list(set(imp.module for imp in imports if imp.module))
        except Exception:
            return []

    def _parse_python(self, content: str) -> List[ImportInfo]:
        """Parse Python import statements."""
        imports = []

        # Handle 'from X import Y' style
        for match in self.PYTHON_FROM_IMPORT.finditer(content):
            dots = match.group(1) or ''
            module = match.group(2) or ''
            members_str = match.group(3)

            full_module = dots + module if module else dots
            is_relative = bool(dots)

            # Parse members (could be multiple, comma-separated)
            members = []
            for m in members_str.split(','):
                m = m.strip()
                if ' as ' in m:
                    name, _ = m.split(' as ')
                    members.append(name.strip())
                else:
                    members.append(m)

            imports.append(ImportInfo(
                module=full_module,
                members=members,
                is_relative=is_relative,
                raw_statement=match.group(0)
            ))

        # Handle simple 'import X' style (exclude 'from' imports already captured)
        simple_import = re.compile(r'^import\s+([\w.]+)(?:\s+as\s+(\w+))?$', re.MULTILINE)
        for match in simple_import.finditer(content):
            module = match.group(1)
            alias = match.group(2)
            imports.append(ImportInfo(
                module=module,
                alias=alias,
                raw_statement=match.group(0)
            ))

        return imports

    def _parse_javascript(self, content: str) -> List[ImportInfo]:
        """Parse JavaScript/TypeScript import statements."""
        imports = []

        # Default imports: import X from 'module'
        for match in self.JS_IMPORT_DEFAULT.finditer(content):
            imports.append(ImportInfo(
                module=match.group(2),
                alias=match.group(1),
                raw_statement=match.group(0)
            ))

        # Named imports: import { X, Y } from 'module'
        for match in self.JS_IMPORT_NAMED.finditer(content):
            members = [m.strip().split(' as ')[0].strip() for m in match.group(1).split(',')]
            imports.append(ImportInfo(
                module=match.group(2),
                members=members,
                raw_statement=match.group(0)
            ))

        # Namespace imports: import * as X from 'module'
        for match in self.JS_IMPORT_ALL.finditer(content):
            imports.append(ImportInfo(
                module=match.group(2),
                alias=match.group(1),
                raw_statement=match.group(0)
            ))

        # Side-effect imports: import 'module'
        for match in self.JS_IMPORT_SIDE_EFFECT.finditer(content):
            imports.append(ImportInfo(
                module=match.group(1),
                raw_statement=match.group(0)
            ))

        # CommonJS require: const X = require('module')
        for match in self.JS_REQUIRE.finditer(content):
            destructured = match.group(1)
            default_name = match.group(2)
            module = match.group(3)

            members = []
            if destructured:
                members = [m.strip().split(':')[0].strip() for m in destructured.split(',')]

            imports.append(ImportInfo(
                module=module,
                alias=default_name,
                members=members,
                raw_statement=match.group(0)
            ))

        # Dynamic imports: import('module')
        for match in self.JS_DYNAMIC_IMPORT.finditer(content):
            imports.append(ImportInfo(
                module=match.group(1),
                raw_statement=match.group(0)
            ))

        return imports

    def _parse_go(self, content: str) -> List[ImportInfo]:
        """Parse Go import statements."""
        imports = []

        # Single imports: import "module" or import alias "module"
        for match in self.GO_IMPORT_SINGLE.finditer(content):
            imports.append(ImportInfo(
                module=match.group(2),
                alias=match.group(1),
                raw_statement=match.group(0)
            ))

        # Import blocks: import ( ... )
        for block_match in self.GO_IMPORT_BLOCK.finditer(content):
            block_content = block_match.group(1)
            for line_match in self.GO_IMPORT_LINE.finditer(block_content):
                imports.append(ImportInfo(
                    module=line_match.group(2),
                    alias=line_match.group(1),
                    raw_statement=line_match.group(0)
                ))

        return imports

    def _parse_java(self, content: str) -> List[ImportInfo]:
        """Parse Java import statements."""
        imports = []

        for match in self.JAVA_IMPORT.finditer(content):
            module = match.group(1)
            imports.append(ImportInfo(
                module=module,
                raw_statement=match.group(0)
            ))

        return imports

    def _parse_rust(self, content: str) -> List[ImportInfo]:
        """Parse Rust use statements."""
        imports = []

        for match in self.RUST_USE.finditer(content):
            module = match.group(1)
            # Extract base module (before :: or {)
            base_module = module.split('::')[0]
            imports.append(ImportInfo(
                module=base_module,
                raw_statement=match.group(0)
            ))

        return imports

    def _parse_c(self, content: str) -> List[ImportInfo]:
        """Parse C/C++ include statements."""
        imports = []

        for match in self.C_INCLUDE.finditer(content):
            header = match.group(1)
            imports.append(ImportInfo(
                module=header,
                raw_statement=match.group(0)
            ))

        return imports

    def _parse_ruby(self, content: str) -> List[ImportInfo]:
        """Parse Ruby require statements."""
        imports = []

        for match in self.RUBY_REQUIRE.finditer(content):
            imports.append(ImportInfo(
                module=match.group(1),
                raw_statement=match.group(0)
            ))

        return imports

    def _parse_php(self, content: str) -> List[ImportInfo]:
        """Parse PHP use/require statements."""
        imports = []

        for match in self.PHP_USE.finditer(content):
            imports.append(ImportInfo(
                module=match.group(1),
                alias=match.group(2),
                raw_statement=match.group(0)
            ))

        for match in self.PHP_REQUIRE.finditer(content):
            imports.append(ImportInfo(
                module=match.group(1),
                raw_statement=match.group(0)
            ))

        return imports
