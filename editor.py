#!/usr/bin/env python3
"""
Simple TUI code editor with syntax highlighting.
Usage: python editor.py <file_path>
"""

import sys
import os
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Footer, TextArea
from textual.reactive import reactive
from textual.binding import Binding

from pygments.lexers import get_lexer_for_filename
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
    """

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, file_path: Optional[str] = None):
        super().__init__()
        self.file_path = file_path
        self.original_content = ""
        self.current_content = ""
        self.language = "Text"

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

        # Load file if provided
        if self.file_path and os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.original_content = content
                self.current_content = content
                editor.text = content
                status_bar.set_file_path(self.file_path)

                # Detect language from file extension
                try:
                    lexer = get_lexer_for_filename(self.file_path)
                    self.language = lexer.name
                    status_bar.set_language(self.language)
                except ClassNotFound:
                    self.language = "Text"
                    status_bar.set_language("Text")

                # Update line numbers
                line_count = len(content.split("\n"))
                line_numbers.update_lines(line_count, 1)

            except Exception as e:
                editor.text = f"# Error loading file: {e}\n# Starting with empty file"
                status_bar.set_file_path(self.file_path or "Untitled")
        else:
            status_bar.set_file_path(self.file_path or "Untitled")
            editor.text = ""

        # Subscribe to text changes
        editor.text = editor.text  # Trigger initial update

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
            # For MVP, save as untitled.txt in current directory
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

    def action_quit(self) -> None:
        """Quit the application."""
        editor = self.query_one("#editor", TextArea)

        # Check for unsaved changes
        if editor.text != self.original_content:
            # For MVP, just show notification and quit
            self.notify("Unsaved changes!", severity="warning", timeout=2)

        self.exit()


def main():
    """Main entry point."""
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    app = CodeEditor(file_path)
    app.run()


if __name__ == "__main__":
    main()
