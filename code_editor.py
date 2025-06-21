"""
MITO Engine - Code Editor
Advanced code editing system with syntax highlighting, auto-completion, and file management
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import re
import mimetypes


class CodeEditor:
    """Advanced code editor with multiple language support"""

    def __init__(self):
        self.language_mappings = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.json': 'json',
            '.md': 'markdown',
            '.txt': 'text',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.xml': 'xml',
            '.sql': 'sql',
            '.sh': 'bash',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.vue': 'vue',
            '.scss': 'scss',
            '.less': 'less',
            '.r': 'r',
            '.scala': 'scala',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.dart': 'dart'
        }

        self.python_keywords = [
            'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del',
            'elif', 'else', 'except', 'exec', 'finally', 'for', 'from',
            'global', 'if', 'import', 'in', 'is', 'lambda', 'not', 'or',
            'pass', 'print', 'raise', 'return', 'try', 'while', 'with',
            'yield', 'True', 'False', 'None', 'async', 'await', 'nonlocal'
        ]

        self.javascript_keywords = [
            'abstract', 'arguments', 'await', 'boolean', 'break', 'byte',
            'case', 'catch', 'char', 'class', 'const', 'continue', 'debugger',
            'default', 'delete', 'do', 'double', 'else', 'enum', 'eval',
            'export', 'extends', 'false', 'final', 'finally', 'float', 'for',
            'function', 'goto', 'if', 'implements', 'import', 'in',
            'instanceof', 'int', 'interface', 'let', 'long', 'native', 'new',
            'null', 'package', 'private', 'protected', 'public', 'return',
            'short', 'static', 'super', 'switch', 'synchronized', 'this',
            'throw', 'throws', 'transient', 'true', 'try', 'typeof', 'var',
            'void', 'volatile', 'while', 'with', 'yield'
        ]

        self.current_files = {}
        self.file_history = {}

    def open_file(self, file_path: str) -> Dict[str, Any]:
        """Open file for editing"""
        try:
            path = Path(file_path)

            if not path.exists():
                return {"success": False, "error": "File does not exist"}

            if path.is_dir():
                return {"success": False, "error": "Path is a directory"}

            # Determine if file is binary
            with open(path, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:
                    return {
                        "success": False,
                        "error": "Cannot edit binary file"
                    }

            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Detect language
            language = self.detect_language(path)

            # Store file info
            file_info = {
                "path":
                str(path),
                "content":
                content,
                "language":
                language,
                "original_content":
                content,
                "modified":
                False,
                "line_count":
                len(content.splitlines()),
                "size":
                len(content),
                "opened_at":
                datetime.now().isoformat(),
                "last_modified":
                datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            }

            self.current_files[str(path)] = file_info

            return {
                "success": True,
                "file_info": file_info,
                "syntax_info": self.get_syntax_info(language)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_file(self, file_path: str, content: str = None) -> Dict[str, Any]:
        """Save file content"""
        try:
            if file_path not in self.current_files:
                if content is None:
                    return {
                        "success": False,
                        "error": "File not open in editor"
                    }
                # Create new file
                return self.create_file(file_path, content)

            file_info = self.current_files[file_path]

            if content is not None:
                file_info["content"] = content

            # Write to disk
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info["content"])

            # Update file info
            file_info["original_content"] = file_info["content"]
            file_info["modified"] = False
            file_info["line_count"] = len(file_info["content"].splitlines())
            file_info["size"] = len(file_info["content"])
            file_info["last_saved"] = datetime.now().isoformat()

            return {
                "success": True,
                "message": f"File {file_path} saved successfully",
                "size": file_info["size"],
                "lines": file_info["line_count"]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_file(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """Create new file"""
        try:
            path = Path(file_path)

            # Create directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Open in editor
            return self.open_file(str(path))

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_content(self, file_path: str, content: str) -> Dict[str, Any]:
        """Update file content in editor"""
        try:
            if file_path not in self.current_files:
                return {"success": False, "error": "File not open in editor"}

            file_info = self.current_files[file_path]
            file_info["content"] = content
            file_info["modified"] = content != file_info["original_content"]
            file_info["line_count"] = len(content.splitlines())
            file_info["size"] = len(content)

            return {
                "success": True,
                "modified": file_info["modified"],
                "lines": file_info["line_count"],
                "size": file_info["size"]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_file_content(self, file_path: str) -> Dict[str, Any]:
        """Get current file content from editor"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        return {
            "success": True,
            "content": file_info["content"],
            "modified": file_info["modified"],
            "language": file_info["language"],
            "lines": file_info["line_count"],
            "size": file_info["size"]
        }

    def close_file(self, file_path: str) -> Dict[str, Any]:
        """Close file in editor"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        modified = file_info["modified"]

        # Store in history
        self.file_history[file_path] = {
            "closed_at": datetime.now().isoformat(),
            "was_modified": modified
        }

        del self.current_files[file_path]

        return {
            "success": True,
            "message": f"File {file_path} closed",
            "was_modified": modified
        }

    def list_open_files(self) -> List[Dict[str, Any]]:
        """List all open files"""
        files = []
        for path, info in self.current_files.items():
            files.append({
                "path": path,
                "language": info["language"],
                "modified": info["modified"],
                "lines": info["line_count"],
                "size": info["size"],
                "opened_at": info["opened_at"]
            })
        return files

    def detect_language(self, path: Path) -> str:
        """Detect programming language from file extension"""
        suffix = path.suffix.lower()
        return self.language_mappings.get(suffix, 'text')

    def get_syntax_info(self, language: str) -> Dict[str, Any]:
        """Get syntax highlighting information for language"""
        syntax_info = {
            "language": language,
            "keywords": [],
            "comment_single": "",
            "comment_multi_start": "",
            "comment_multi_end": "",
            "string_delimiters": ["'", '"'],
            "bracket_pairs": [["(", ")"], ["[", "]"], ["{", "}"]]
        }

        if language == "python":
            syntax_info.update({
                "keywords": self.python_keywords,
                "comment_single": "#",
                "comment_multi_start": '"""',
                "comment_multi_end": '"""',
                "indent_size": 4,
                "use_tabs": False
            })
        elif language == "javascript":
            syntax_info.update({
                "keywords": self.javascript_keywords,
                "comment_single": "//",
                "comment_multi_start": "/*",
                "comment_multi_end": "*/",
                "indent_size": 2,
                "use_tabs": False
            })
        elif language == "html":
            syntax_info.update({
                "comment_single": "",
                "comment_multi_start": "<!--",
                "comment_multi_end": "-->",
                "tag_start": "<",
                "tag_end": ">",
                "indent_size": 2,
                "use_tabs": False
            })
        elif language == "css":
            syntax_info.update({
                "comment_single": "",
                "comment_multi_start": "/*",
                "comment_multi_end": "*/",
                "indent_size": 2,
                "use_tabs": False
            })

        return syntax_info

    def format_code(self, file_path: str) -> Dict[str, Any]:
        """Auto-format code based on language"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        language = file_info["language"]
        content = file_info["content"]

        try:
            if language == "python":
                formatted_content = self.format_python(content)
            elif language == "javascript":
                formatted_content = self.format_javascript(content)
            elif language == "json":
                # Parse and re-format JSON
                data = json.loads(content)
                formatted_content = json.dumps(data,
                                               indent=2,
                                               ensure_ascii=False)
            else:
                # Basic formatting for other languages
                formatted_content = self.basic_format(content)

            # Update content
            result = self.update_content(file_path, formatted_content)
            if result["success"]:
                result["message"] = f"Code formatted for {language}"

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Error formatting code: {str(e)}"
            }

    def format_python(self, content: str) -> str:
        """Basic Python formatting"""
        lines = content.splitlines()
        formatted_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append("")
                continue

            # Decrease indent for certain keywords
            if stripped.startswith(('except', 'elif', 'else', 'finally')):
                current_indent = max(0, indent_level - 1)
            else:
                current_indent = indent_level

            # Add formatted line
            formatted_lines.append('    ' * current_indent + stripped)

            # Increase indent after certain keywords
            if stripped.endswith(':') and any(
                    stripped.startswith(kw) for kw in [
                        'def ', 'class ', 'if ', 'elif ', 'else:', 'for ',
                        'while ', 'try:', 'except', 'finally:', 'with '
                    ]):
                indent_level += 1

            # Decrease indent after certain patterns
            if stripped in ['pass', 'break', 'continue', 'return', 'raise'
                            ] or stripped.startswith(
                                'return ') or stripped.startswith('raise '):
                indent_level = max(0, indent_level - 1)

        return '\n'.join(formatted_lines)

    def format_javascript(self, content: str) -> str:
        """Basic JavaScript formatting"""
        lines = content.splitlines()
        formatted_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append("")
                continue

            # Decrease indent for closing braces
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)

            # Add formatted line
            formatted_lines.append('  ' * indent_level + stripped)

            # Increase indent after opening braces
            if stripped.endswith('{'):
                indent_level += 1

        return '\n'.join(formatted_lines)

    def basic_format(self, content: str) -> str:
        """Basic formatting for any text"""
        lines = content.splitlines()
        formatted_lines = []

        for line in lines:
            # Remove trailing whitespace and normalize line endings
            formatted_lines.append(line.rstrip())

        # Remove multiple consecutive empty lines
        result_lines = []
        prev_empty = False

        for line in formatted_lines:
            if line.strip() == "":
                if not prev_empty:
                    result_lines.append("")
                prev_empty = True
            else:
                result_lines.append(line)
                prev_empty = False

        return '\n'.join(result_lines)

    def get_line_info(self, file_path: str,
                      line_number: int) -> Dict[str, Any]:
        """Get information about a specific line"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        lines = file_info["content"].splitlines()

        if line_number < 1 or line_number > len(lines):
            return {"success": False, "error": "Line number out of range"}

        line_content = lines[line_number - 1]

        return {
            "success": True,
            "line_number": line_number,
            "content": line_content,
            "length": len(line_content),
            "indentation": len(line_content) - len(line_content.lstrip()),
            "is_empty": line_content.strip() == ""
        }

    def find_in_file(self,
                     file_path: str,
                     search_term: str,
                     case_sensitive: bool = False) -> Dict[str, Any]:
        """Find text in file"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        content = file_info["content"]

        if not case_sensitive:
            content_search = content.lower()
            search_term_search = search_term.lower()
        else:
            content_search = content
            search_term_search = search_term

        lines = content.splitlines()
        matches = []

        for i, line in enumerate(lines, 1):
            line_search = line.lower() if not case_sensitive else line
            if search_term_search in line_search:
                start_pos = line_search.find(search_term_search)
                matches.append({
                    "line": i,
                    "column": start_pos + 1,
                    "text": line,
                    "match_start": start_pos,
                    "match_end": start_pos + len(search_term)
                })

        return {
            "success": True,
            "search_term": search_term,
            "case_sensitive": case_sensitive,
            "matches": matches,
            "total_matches": len(matches)
        }

    def get_autocomplete_suggestions(self, file_path: str, line: int,
                                     column: int) -> Dict[str, Any]:
        """Get autocomplete suggestions"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        language = file_info["language"]

        suggestions = []

        if language == "python":
            suggestions.extend(self.python_keywords)
            # Add common Python built-ins
            suggestions.extend([
                'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'tuple',
                'set'
            ])
        elif language == "javascript":
            suggestions.extend(self.javascript_keywords)
            # Add common JavaScript methods
            suggestions.extend([
                'console.log', 'document.getElementById', 'addEventListener',
                'querySelector'
            ])

        return {
            "success": True,
            "language": language,
            "suggestions": suggestions[:20]  # Limit to 20 suggestions
        }

    def format_javascript(self, content: str) -> str:
        """Basic JavaScript formatting"""
        lines = content.splitlines()
        formatted_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append("")
                continue

            # Decrease indent for closing braces
            if stripped.startswith('}'):
                indent_level = max(0, indent_level - 1)

            formatted_lines.append("  " * indent_level + stripped)

            # Increase indent for opening braces
            if stripped.endswith('{'):
                indent_level += 1
            elif stripped.startswith('}'):
                pass  # Already handled above

        return "\n".join(formatted_lines)

    def basic_format(self, content: str) -> str:
        """Basic formatting for unknown languages"""
        lines = content.splitlines()
        # Remove trailing whitespace and normalize line endings
        return "\n".join(line.rstrip() for line in lines)

    def find_and_replace(self,
                         file_path: str,
                         find_text: str,
                         replace_text: str,
                         case_sensitive: bool = True,
                         regex: bool = False) -> Dict[str, Any]:
        """Find and replace text in file"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        content = file_info["content"]

        try:
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                new_content = re.sub(find_text,
                                     replace_text,
                                     content,
                                     flags=flags)
                matches = len(re.findall(find_text, content, flags=flags))
            else:
                if case_sensitive:
                    matches = content.count(find_text)
                    new_content = content.replace(find_text, replace_text)
                else:
                    # Case insensitive replacement
                    matches = content.lower().count(find_text.lower())
                    pattern = re.compile(re.escape(find_text), re.IGNORECASE)
                    new_content = pattern.sub(replace_text, content)

            if matches > 0:
                self.update_content(file_path, new_content)

            return {
                "success": True,
                "matches": matches,
                "message": f"Replaced {matches} occurrences"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_line_info(self, file_path: str,
                      line_number: int) -> Dict[str, Any]:
        """Get information about a specific line"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        lines = file_info["content"].splitlines()

        if line_number < 1 or line_number > len(lines):
            return {"success": False, "error": "Line number out of range"}

        line_content = lines[line_number - 1]

        return {
            "success": True,
            "line_number": line_number,
            "content": line_content,
            "length": len(line_content),
            "indent_level": len(line_content) - len(line_content.lstrip()),
            "is_empty": line_content.strip() == ""
        }

    def insert_line(self, file_path: str, line_number: int,
                    content: str) -> Dict[str, Any]:
        """Insert line at specific position"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        lines = file_info["content"].splitlines()

        if line_number < 1 or line_number > len(lines) + 1:
            return {"success": False, "error": "Line number out of range"}

        lines.insert(line_number - 1, content)
        new_content = "\n".join(lines)

        result = self.update_content(file_path, new_content)
        if result["success"]:
            result["message"] = f"Line inserted at position {line_number}"

        return result

    def delete_line(self, file_path: str, line_number: int) -> Dict[str, Any]:
        """Delete line at specific position"""
        if file_path not in self.current_files:
            return {"success": False, "error": "File not open in editor"}

        file_info = self.current_files[file_path]
        lines = file_info["content"].splitlines()

        if line_number < 1 or line_number > len(lines):
            return {"success": False, "error": "Line number out of range"}

        deleted_content = lines.pop(line_number - 1)
        new_content = "\n".join(lines)

        result = self.update_content(file_path, new_content)
        if result["success"]:
            result["message"] = f"Line {line_number} deleted"
            result["deleted_content"] = deleted_content

        return result


# Global code editor instance
code_editor = CodeEditor()


def main():
    """Demo of code editor functionality"""

    # Create a test file
    result = code_editor.create_file("test_editor.py",
                                     "print('Hello MITO Engine!')\n")
    print("Create file:", json.dumps(result, indent=2))

    # Update content
    new_content = """def hello_mito():
    print('Hello MITO Engine!')
    return 'success'

if __name__ == '__main__':
    result = hello_mito()
    print(f'Result: {result}')
"""

    update_result = code_editor.update_content("test_editor.py", new_content)
    print("Update content:", json.dumps(update_result, indent=2))

    # Format code
    format_result = code_editor.format_code("test_editor.py")
    print("Format code:", json.dumps(format_result, indent=2))

    # Save file
    save_result = code_editor.save_file("test_editor.py")
    print("Save file:", json.dumps(save_result, indent=2))


if __name__ == "__main__":
    main()
