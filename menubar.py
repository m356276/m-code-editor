from curses import window
from PySide6.QtGui import QAction


def create_menubar(window):
    menu = window.menuBar()

    file_menu = menu.addMenu("File")
    edit_menu = menu.addMenu("Edit")
    terminal_menu = menu.addMenu("Terminal")
    help_menu = menu.addMenu("Help")

    # ---------- File ----------
    open_file_action = QAction("Open file", window)
    open_folder_action = QAction("Open folder", window)
    save_action = QAction("Save", window)
    exit_action = QAction("Exit", window)

    open_file_action.triggered.connect(
        lambda: hasattr(window, "open_file_dialog") and window.open_file_dialog()
    )
    open_folder_action.triggered.connect(
        lambda: hasattr(window, "open_folder_dialog") and window.open_folder_dialog()
    )
    save_action.triggered.connect(
        lambda: hasattr(window, "save_file") and window.save_file()
    )
    exit_action.triggered.connect(window.close)

    file_menu.addActions([open_file_action, open_folder_action, save_action])
    file_menu.addSeparator()
    file_menu.addAction(exit_action)

    # ---------- Edit ----------
    undo_action = QAction("Undo", window)
    redo_action = QAction("Redo", window)
    copy_action = QAction("Copy", window)
    paste_action = QAction("Paste", window)

    undo_action.setShortcut("Ctrl+Z")
    redo_action.setShortcut("Ctrl+Shift+Z")
    copy_action.setShortcut("Ctrl+C")
    paste_action.setShortcut("Ctrl+V")

    if hasattr(window, "editor"):
        undo_action.triggered.connect(window.editor.undo)
        redo_action.triggered.connect(window.editor.redo)
        copy_action.triggered.connect(window.editor.copy)
        paste_action.triggered.connect(window.editor.paste)

    edit_menu.addActions([undo_action, redo_action, copy_action, paste_action])

    # ---------- Terminal ----------
    new_terminal_action = QAction("New Terminal", window)
    new_terminal_action.triggered.connect(
        lambda: hasattr(window, "open_terminal") and window.open_terminal()
    )
    terminal_menu.addAction(new_terminal_action)

    # ---------- Help ----------
    help_menu.addAction(QAction("Website(Soon)", window))
    help_menu.addAction(QAction("About", window))


    run_action = QAction("Run", window)
    run_action.setShortcut("F5")

    if hasattr(window, "run_current_file"):
        run_action.triggered.connect(window.run_current_file)
    
    terminal_menu.addAction(run_action)

    return menu
