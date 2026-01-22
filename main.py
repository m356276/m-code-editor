import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPlainTextEdit,
    QTreeView,
    QFileSystemModel,
    QSplitter,
    QWidget,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QToolBar,
    QSizePolicy,
    QInputDialog
)
from PySide6.QtGui import (
    QFont,
    QAction,
    QColor,
    QPainter,
    QTextFormat,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor
    
)
from PySide6.QtCore import Qt, QRect, QSize, QRegularExpression, QProcess
from menubar import create_menubar
import subprocess


# ================= Syntax Highlighter =================


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))  # Blue
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and",
            "as",
            "assert",
            "break",
            "class",
            "continue",
            "def",
            "del",
            "elif",
            "else",
            "except",
            "False",
            "finally",
            "for",
            "from",
            "global",
            "import",
            "in",
            "is",
            "lambda",
            "None",
            "nonlocal",
            "not",
            "or",
            "pass",
            "raise",
            "return",
            "True",
            "try",
            "with",
            "yield",
        ]
        self.highlighting_rules = [
            (QRegularExpression(r"\b" + keyword + r"\b"), keyword_format)
            for keyword in keywords
        ]

        # Special keywords: if and while
        special_keyword_format = QTextCharFormat()
        special_keyword_format.setForeground(QColor("#c586c0"))  # Purple
        special_keyword_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((QRegularExpression(r"\bif\b"), special_keyword_format))
        self.highlighting_rules.append((QRegularExpression(r"\bwhile\b"), special_keyword_format))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))  # Orange
        self.highlighting_rules.append((QRegularExpression(r'".*"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*'"), string_format))
        # Multi-line strings
        multi_string_format = QTextCharFormat()
        multi_string_format.setForeground(QColor("#ce9178"))  # Orange
        multi_string_regex = QRegularExpression(r'""".*"""')
        multi_string_regex.setPatternOptions(QRegularExpression.PatternOption.DotMatchesEverythingOption)
        self.highlighting_rules.append((multi_string_regex, multi_string_format))
        multi_string_regex2 = QRegularExpression(r"'''.*'''")
        multi_string_regex2.setPatternOptions(QRegularExpression.PatternOption.DotMatchesEverythingOption)
        self.highlighting_rules.append((multi_string_regex2, multi_string_format))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))  # Green
        self.highlighting_rules.append((QRegularExpression(r"#.*"), comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))  # Light green
        self.highlighting_rules.append((QRegularExpression(r"\b\d+\b"), number_format))

        # Functions
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))  # Yellow
        self.highlighting_rules.append(
            (QRegularExpression(r"\bdef\b"), function_format)
        )

        # Print
        print_format = QTextCharFormat()
        print_format.setForeground(QColor("#dcdcaa"))  # Yellow
        self.highlighting_rules.append((QRegularExpression(r"\bprint\b"), print_format))


        # Classes
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4ec9b0"))  # Teal
        self.highlighting_rules.append(
            (QRegularExpression(r"\bclass\s+(\w+)"), class_format)
        )

        # Self
        self_format = QTextCharFormat()
        self_format.setForeground(QColor("#c586c0"))  # Purple
        self.highlighting_rules.append((QRegularExpression(r"\bself\b"), self_format))

        # Decorators
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#d4d4aa"))  # Light yellow
        self.highlighting_rules.append((QRegularExpression(r"@\w+"), decorator_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


# ================= Line Number Area =================


# ================= Line Number Area =================


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


# ================= Code Editor =================


class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        font = QFont("JetBrains Mono")
        font.setPointSize(11)
        self.setFont(font)

        # Dark gray theme with accents: background, text and selection
        self.setStyleSheet(
            "background-color: #252525; color: #d0d0d0; padding-left: 4px;"
            "selection-background-color: #007acc;"  # Blue accent

        )

        self.highlighter = PythonHighlighter(self.document())

        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    # ---------- Line Numbers ----------

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance("9") * digits

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(30, 30, 30))  # Dark gray background

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(136, 136, 136))  # Gray text
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    # ---------- Current Line Highlight ----------

    def highlight_current_line(self):
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor(40, 40, 40))  # Slightly lighter gray
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    # ---------- Auto Indentation(Einrückung) ----------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            cursor = self.textCursor()
            current_block = cursor.block()
            text = current_block.text()
            indent = len(text) - len(text.lstrip())
            indent_str = ' ' * indent
            # If the line ends with ':', increase indentation
            if text.strip().endswith(':'):
                indent_str += '    '
            cursor.insertText('\n' + indent_str)
            event.accept()
        else:
            super().keyPressEvent(event)


# ================= Terminal Widget =================


class TerminalWidget(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        font = QFont("JetBrains Mono")
        font.setPointSize(11)
        self.setFont(font)

        self.setStyleSheet(
            "background-color: #1a1a1a; color: #d0d0d0; border: none;"
        )

        self.setMaximumHeight(200)  # Initial height

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.finished.connect(self.process_finished)

        self.start_shell()

    def start_shell(self):
        self.process.start("zsh", [])  # Or "bash" if preferred

    def read_output(self):
        output = self.process.readAllStandardOutput().data().decode()
        self.insertPlainText(output)
        self.moveCursor(QTextCursor.End)

    def read_error(self):
        error = self.process.readAllStandardError().data().decode()
        self.insertPlainText(error)
        self.moveCursor(QTextCursor.End)

    def process_finished(self):
        self.insertPlainText("\n[Process finished]\n")
        self.moveCursor(QTextCursor.End)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            # Get the current line
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.select(QTextCursor.LineUnderCursor)
            command = cursor.selectedText().strip()
            self.insertPlainText("\n")
            if command:
                self.process.write((command + "\n").encode())
            else:
                self.process.write("\n".encode())
        else:
            super().keyPressEvent(event)


# ================= Main Window =================


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("M Code Editor")
        self.resize(1920, 1080)
        self.setStyleSheet("background-color: #1a1a1a; color: #d0d0d0;")
        self.current_file_path = None

        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(
            "QSplitter::handle { background-color: #404040; border: 1px solid #606060; }"
            "QSplitter::handle:horizontal { width: 2px; }"
            "QSplitter::handle:vertical { height: 2px; }"
        )

        self.editor = CodeEditor()

        # ---------- Sidebar ----------
        self.model = QFileSystemModel()
        self.model.setRootPath(".")

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index("."))
        self.tree.setHeaderHidden(True)
        self.tree.setColumnWidth(0, 250)
        self.tree.setStyleSheet(
            "background-color: #1a1a1a; color: #d0d0d0; border: none;"
            "selection-background-color: #007acc;"
        )
        self.tree.doubleClicked.connect(self.open_file)

        # Vertical splitter for editor and terminal
        editor_terminal_splitter = QSplitter(Qt.Vertical)
        editor_terminal_splitter.addWidget(self.editor)

        self.terminal = TerminalWidget()
        self.terminal.hide()  # Initially hidden
        editor_terminal_splitter.addWidget(self.terminal)

        splitter.addWidget(self.tree)
        splitter.addWidget(editor_terminal_splitter)
        splitter.setSizes([150, 750])
        self.setCentralWidget(splitter)

        # ---------- Menu (extracted to menubar.py) ----------
        create_menubar(self)
        self.menuBar().setStyleSheet(
            "QMenuBar { background-color: #1a1a1a; color: #d0d0d0; border-bottom: 1px solid #404040; }"
            "QMenuBar::item { background-color: transparent; padding: 4px 8px; }"
            "QMenuBar::item:selected { background-color: #2a2a2a; }"
            "QMenu { background-color: #1a1a1a; color: #d0d0d0; border: 1px solid #404040; }"
            "QMenu::item { padding: 4px 20px; }"
            "QMenu::item:selected { background-color: #2a2a2a; }"
        )

        # ---------- Toolbar ----------
        


        toolbar = self.addToolBar("Run")
        toolbar.setMovable(False)

        new_file_button = QPushButton("New File")
        new_file_button.setStyleSheet(
            "QPushButton { background-color: #007acc; color: white; padding: 4px 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #005a9e; }"
        )
        new_file_button.setToolTip("Create New File")
        toolbar.addWidget(new_file_button)
        new_file_button.clicked.connect(self.new_file)

        new_folder_button = QPushButton("New Folder")
        new_folder_button.setStyleSheet(
            "QPushButton { background-color: #007acc; color: white; padding: 4px 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #005a9e; }"
        )
        new_folder_button.setToolTip("Create New Folder")
        toolbar.addWidget(new_folder_button)
        new_folder_button.clicked.connect(self.new_folder)

        spacer_left = QWidget()
        spacer_left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer_left)
        run_button = QPushButton("▶ Run")
        run_button.setStyleSheet(
            "QPushButton { background-color: #007acc; color: white; padding: 4px 8px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #005a9e; }"
        )
        run_button.setShortcut("F5")
        run_button.clicked.connect(self.run_current_file)
        toolbar.addWidget(run_button)
        spacer_right = QWidget()
        spacer_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer_right)

        
    


    def open_file(self, index):
        if self.model.isDir(index):
            # Expand or collapse the folder
            if self.tree.isExpanded(index):
                self.tree.collapse(index)
            else:
                self.tree.expand(index)
            return

        path = self.model.filePath(index)
        if not path.endswith((".py", ".txt", ".html")):
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.editor.setPlainText(f.read())
            self.current_file_path = path
            self.setWindowTitle(f"M Code Editor - {path}")
            # Highlight the file in the tree
            self.tree.setCurrentIndex(index)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*);;Python Files (*.py);;Text Files (*.txt)",
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
                self.current_file_path = file_path
                self.setWindowTitle(f"M Code Editor - {file_path}")
                # Update tree to show the file's directory and select the file
                import os

                dir_path = os.path.dirname(file_path)
                self.model.setRootPath(dir_path)
                self.tree.setRootIndex(self.model.index(dir_path))
                file_index = self.model.index(file_path)
                self.tree.setCurrentIndex(file_index)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder_path:
            self.model.setRootPath(folder_path)
            self.tree.setRootIndex(self.model.index(folder_path))

    def new_file(self):
        file_name, ok = QInputDialog.getText(self, "New File", "File Name:")
        if ok and file_name:
            import os

            root_path = self.model.rootPath()
            new_file_path = os.path.join(root_path, file_name)
            try:
                with open(new_file_path, "w", encoding="utf-8") as f:
                    f.write("")  # Create an empty file
                # Refresh the tree view
                self.tree.update()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create file: {e}")

    def new_folder(self):
        folder_name, ok = QInputDialog.getText(self, "New Folder", "Folder Name:")
        if ok and folder_name:
            import os
            root_path = self.model.rootPath()
            new_folder_path = os.path.join(root_path, folder_name)
            try:
                os.makedirs(new_folder_path, exist_ok=True)
                # Refresh the tree view
                self.tree.update()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create folder: {e}")

    def open_terminal(self):
        if self.terminal.isHidden():
            self.terminal.show()
        else:
            self.terminal.hide()

    def save_file(self):
        if self.current_file_path:
            try:
                with open(self.current_file_path, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                QMessageBox.information(self, "Saved", "File saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            "",
            "All Files (*);;Python Files (*.py);;Text Files (*.txt)",
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                self.current_file_path = file_path
                self.setWindowTitle(f"M Code Editor - {file_path}")
                QMessageBox.information(self, "Saved", "File saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file: {e}")

    # ----- run current file (MENU BAR) ---------

    def run_current_file(self):
        if not self.current_file_path:
            QMessageBox.warning(self, "Run", "No file opened")
            return

        if not self.current_file_path.endswith(".py"):
            QMessageBox.warning(self, "Run", "Only Python files supported")
            return
        try:
            result = subprocess.run(
                [sys.executable, self.current_file_path], capture_output=True, text=True
            )

            output = result.stdout + result.stderr
            self.terminal.show()
            self.terminal.insertPlainText(output + "\n")
            self.terminal.moveCursor(QTextCursor.End)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ================= Main =================


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
