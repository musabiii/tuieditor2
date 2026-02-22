#!/usr/bin/env python3
"""
Simple TUI code editor with syntax highlighting.
Usage: python editor.py <file_path>
"""

import sys
import os
from pathlib import Path
from typing import Optional, Tuple

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Static, Footer, TextArea, Input, Button
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import ModalScreen

from pygments.lexers import get_lexer_for_filename, get_lexer_by_name
from pygments.util import ClassNotFound


class LineNumbers(Static):
    """Widget for displaying line numbers."""

    lines_count = reactive(1)
    current_line = reactive(1)

    def compose(self) -> ComposeResult:
        yield Static("1", id="line-numbers-content")

    def watch_lines_count(self, count: int) -> None:
        self._update_content()

    def watch_current_line(self, line: int) -> None:
        self._update_content()

    def _update_content(self) -> None:
        lines = []
        for i in range(1, self.lines_count + 1):
            prefix = ">" if i == self.current_line else " "
            lines.append(f"{prefix}{i:3}")
        content = "\n".join(lines)
        self.query_one("#line-numbers-content", Static).update(content)

    def update_lines(self, count: int, current: int = 1) -> None:
        self.lines_count = count
        self.current_line = current


class StatusBar(Static):
    """Status bar showing file info."""

    file_path = reactive("")
    cursor_line = reactive(1)
    cursor_col = reactive(1)
    language = reactive("Text")
    modified = reactive(False)

    def compose(self) -> ComposeResult:
        yield Static(id="status-content")

    def watch_file_path(self, path: str) -> None:
        self._update_status()

    def watch_cursor_line(self, line: int) -> None:
        self._update_status()

    def watch_cursor_col(self, col: int) -> None:
        self._update_status()

    def watch_language(self, lang: str) -> None:
        self._update_status()

    def watch_modified(self, modified: bool) -> None:
        self._update_status()

    def _update_status(self) -> None:
        filename = os.path.basename(self.file_path) if self.file_path else "Untitled"
        modified_indicator = " [●]" if self.modified else ""
        content = f"{filename}{modified_indicator} | Line {self.cursor_line}, Col {self.cursor_col} | {self.language}"
        self.query_one("#status-content", Static).update(content)

    def set_file_path(self, path: str) -> None:
        self.file_path = path

    def set_cursor_pos(self, line: int, col: int) -> None:
        self.cursor_line = line
        self.cursor_col = col

    def set_language(self, lang: str) -> None:
        self.language = lang

    def set_modified(self, modified: bool) -> None:
        self.modified = modified


class SearchModal(ModalScreen[Optional[str]]):
    """Modal screen for searching text."""

    DEFAULT_CSS = """
    SearchModal {
        align: center middle;
    }

    #search-container {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #search-input {
        width: 100%;
    }

    #search-label {
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="search-container"):
            yield Static("Search:", id="search-label")
            yield Input(placeholder="Enter search term...", id="search-input")

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class OpenFileModal(ModalScreen[Optional[str]]):
    """Modal screen for opening files."""

    DEFAULT_CSS = """
    OpenFileModal {
        align: center middle;
    }

    #open-container {
        width: 80;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #open-input {
        width: 100%;
    }

    #open-label {
        margin-bottom: 1;
    }

    #open-hint {
        margin-top: 1;
        color: $text-muted;
    }
    """

    def compose(self) -> ComposeResult:
        with Container(id="open-container"):
            yield Static("Open file:", id="open-label")
            yield Input(placeholder="path/to/file", id="open-input")
            yield Static("Press Enter to open, Esc to cancel", id="open-hint")

    def on_mount(self) -> None:
        self.query_one("#open-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self.dismiss(None)


class CodeEditor(App):
    """Simple TUI code editor."""

    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        width: 100%;
        height: 100%;
    }

    #editor-container {
        width: 100%;
        height: 1fr;
    }

    #line-numbers {
        width: 5;
        height: 100%;
        background: $surface-darken-1;
        color: $text-muted;
        text-align: right;
    }

    #line-numbers-content {
        width: 100%;
        height: auto;
    }

    #editor-wrapper {
        width: 1fr;
        height: 100%;
    }

    #editor {
        width: 100%;
        height: 100%;
        border: none;
    }

    #status-bar {
        dock: bottom;
        height: 1;
        background: $surface-darken-2;
        color: $text;
        padding-left: 1;
        padding-right: 1;
    }

    TextArea {
        background: $surface;
        color: $text;
        border: none;
    }

    TextArea:focus {
        border: none;
    }

    TextArea .text-area--cursor {
        background: $primary;
        color: $text;
    }
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+z", "undo", "Undo"),
        Binding("ctrl+y", "redo", "Redo"),
        Binding("ctrl+f", "search", "Search"),
        Binding("ctrl+o", "open_file", "Open"),
    ]

    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        self.file_path = file_path
        self.original_content = ""
        self.current_content = ""
        self.language = "Text"
        self.search_term = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="main-container"):
            with Horizontal(id="editor-container"):
                yield LineNumbers(id="line-numbers")
                with Vertical(id="editor-wrapper"):
                    yield TextArea(id="editor")
            yield StatusBar(id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        """Initialize the editor when app starts."""
        editor = self.query_one("#editor", TextArea)
        status_bar = self.query_one("#status-bar", StatusBar)
        line_numbers = self.query_one("#line-numbers", LineNumbers)

        # Set up editor
        editor.focus()
        editor.show_line_numbers = False  # We use custom line numbers

        # Load file if provided
        if self.file_path and os.path.exists(self.file_path):
            self._load_file(self.file_path)
        else:
            status_bar.set_file_path(self.file_path or "Untitled")
            editor.text = ""
            editor.language = "text"

    def _load_file(self, file_path: str) -> None:
        """Load a file into the editor."""
        editor = self.query_one("#editor", TextArea)
        status_bar = self.query_one("#status-bar", StatusBar)
        line_numbers = self.query_one("#line-numbers", LineNumbers)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.original_content = content
            self.current_content = content
            self.file_path = file_path
            editor.text = content
            status_bar.set_file_path(file_path)

            # Detect language from file extension
            language = self._detect_language(file_path)
            self.language = language
            status_bar.set_language(language)

            # Update line numbers
            line_count = len(content.split("\n"))
            line_numbers.update_lines(line_count, 1)

            self.notify(f"Opened: {file_path}", severity="information", timeout=2)

        except Exception as e:
            editor.text = f"# Error loading file: {e}\n# Starting with empty file"
            status_bar.set_file_path(file_path or "Untitled")
            self.notify(f"Error: {e}", severity="error", timeout=3)

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        try:
            lexer = get_lexer_for_filename(file_path)
            return lexer.name
        except ClassNotFound:
            # Try common extensions
            ext = os.path.splitext(file_path)[1].lower()
            extension_map = {
                ".py": "python",
                ".js": "javascript",
                ".ts": "typescript",
                ".jsx": "jsx",
                ".tsx": "tsx",
                ".html": "html",
                ".htm": "html",
                ".css": "css",
                ".scss": "scss",
                ".sass": "sass",
                ".rs": "rust",
                ".go": "go",
                ".c": "c",
                ".h": "c",
                ".cpp": "cpp",
                ".hpp": "cpp",
                ".java": "java",
                ".kt": "kotlin",
                ".swift": "swift",
                ".rb": "ruby",
                ".php": "php",
                ".sh": "bash",
                ".bash": "bash",
                ".zsh": "zsh",
                ".ps1": "powershell",
                ".json": "json",
                ".xml": "xml",
                ".yaml": "yaml",
                ".yml": "yaml",
                ".toml": "toml",
                ".ini": "ini",
                ".cfg": "ini",
                ".md": "markdown",
                ".sql": "sql",
                ".dockerfile": "dockerfile",
            }
            lang = extension_map.get(ext, "Text")
            try:
                lexer = get_lexer_by_name(lang)
                return lexer.name
            except ClassNotFound:
                return "Text"

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text changes."""
        self.current_content = event.text_area.text
        status_bar = self.query_one("#status-bar", StatusBar)
        line_numbers = self.query_one("#line-numbers", LineNumbers)

        # Update modified status
        is_modified = self.current_content != self.original_content
        status_bar.set_modified(is_modified)

        # Update line numbers
        line_count = max(1, len(self.current_content.split("\n")))
        current_line = (
            event.text_area.cursor_location[0] + 1
            if event.text_area.cursor_location
            else 1
        )
        line_numbers.update_lines(line_count, current_line)

    def on_text_area_cursor_moved(self, event) -> None:
        """Update status bar when cursor moves."""
        editor = self.query_one("#editor", TextArea)
        status_bar = self.query_one("#status-bar", StatusBar)
        line_numbers = self.query_one("#line-numbers", LineNumbers)

        # Get cursor position
        cursor = editor.cursor_location
        if cursor:
            line, col = cursor
            status_bar.set_cursor_pos(line + 1, col + 1)

            # Update current line highlight
            line_count = max(1, len(editor.text.split("\n")))
            line_numbers.update_lines(line_count, line + 1)

    def action_save(self) -> None:
        """Save the file."""
        editor = self.query_one("#editor", TextArea)
        status_bar = self.query_one("#status-bar", StatusBar)

        save_path = self.file_path
        if not save_path or save_path == "Untitled":
            save_path = "untitled.txt"
            self.file_path = save_path

        try:
            content = editor.text
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.original_content = content
            status_bar.set_modified(False)
            status_bar.set_file_path(save_path)
            self.notify(f"Saved: {save_path}", severity="information", timeout=2)
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error", timeout=3)

    def action_undo(self) -> None:
        """Undo last action."""
        editor = self.query_one("#editor", TextArea)
        editor.undo()
        self.notify("Undo", severity="information", timeout=1)

    def action_redo(self) -> None:
        """Redo last undone action."""
        editor = self.query_one("#editor", TextArea)
        editor.redo()
        self.notify("Redo", severity="information", timeout=1)

    def action_search(self) -> None:
        """Open search modal."""

        def handle_search_result(search_term: Optional[str]) -> None:
            if search_term:
                self.search_term = search_term
                self._perform_search(search_term)

        self.push_screen(SearchModal(), handle_search_result)

    def _perform_search(self, search_term: str) -> None:
        """Search for text in editor."""
        editor = self.query_one("#editor", TextArea)
        text = editor.text

        # Simple search - find next occurrence
        cursor = editor.cursor_location
        if cursor is None:
            cursor = (0, 0)

        line, col = cursor
        lines = text.split("\n")

        # Search from current position
        found = False
        for i in range(line, len(lines)):
            search_start = col if i == line else 0
            pos = lines[i].find(search_term, search_start)
            if pos != -1:
                editor.cursor_location = (i, pos)
                found = True
                break

        # Wrap around if not found
        if not found:
            for i in range(0, line):
                pos = lines[i].find(search_term)
                if pos != -1:
                    editor.cursor_location = (i, pos)
                    found = True
                    break

        if found:
            self.notify(f"Found: {search_term}", severity="information", timeout=2)
        else:
            self.notify(f"Not found: {search_term}", severity="warning", timeout=2)

    def action_open_file(self) -> None:
        """Open file dialog."""

        def handle_open_result(file_path: Optional[str]) -> None:
            if file_path:
                if os.path.exists(file_path):
                    self._load_file(file_path)
                else:
                    self.notify(
                        f"File not found: {file_path}", severity="error", timeout=3
                    )

        self.push_screen(OpenFileModal(), handle_open_result)

    def action_quit(self) -> None:
        """Quit the application."""
        editor = self.query_one("#editor", TextArea)

        # Check for unsaved changes
        if editor.text != self.original_content:
            self.notify(
                "Unsaved changes! Press Ctrl+Q again to quit.",
                severity="warning",
                timeout=3,
            )
            # Reset original content so second quit works
            self.original_content = editor.text
        else:
            self.exit()


def main():
    """Main entry point."""
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = CodeEditor(file_path)
    app.run()


if __name__ == "__main__":
    main()
