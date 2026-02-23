import threading
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QMessageBox,
    QFrame,
    QStyle,
)
from PyQt6.QtGui import QAction, QPixmap, QFont, QIcon, QDesktopServices
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QUrl

from .helpers import get_bibtex_for_doi, copy_to_clipboard
from .about_dialog import AboutDialog
from .how_to_use_dialog import HowToUseDialog
from .app_info import LICENSE_PATH, WEBAPP_URL, ISSUES_URL
from .i18n import tr


class FetchWorker(QObject):
    finished = pyqtSignal(bool, str, object)  # found, bibtex, error

    def __init__(self, doi: str):
        super().__init__()
        self.doi = doi

    def run(self):
        try:
            found, bibtex, error = get_bibtex_for_doi(self.doi)
        except Exception as e:
            found, bibtex, error = False, "", str(e)
        self.finished.emit(found, bibtex, error)


class QuickBibWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("window.title"))
        self.resize(500, 380)

        # Set up emoji font support
        self._emoji_font = self._setup_emoji_font()

        central = QWidget()
        self.setCentralWidget(central)

        vbox = QVBoxLayout()
        central.setLayout(vbox)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu(tr("menu.file"))
        quit_action = QAction(tr("action.quit"), self)
        quit_action.setFont(self._emoji_font)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = menubar.addMenu(tr("menu.edit"))
        copy_action = QAction(tr("action.copy_bibtex"), self)
        copy_action.setFont(self._emoji_font)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_to_clipboard)
        edit_menu.addAction(copy_action)

        help_menu = menubar.addMenu(tr("menu.help"))
        about_action = QAction(tr("action.about"), self)
        about_action.setFont(self._emoji_font)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        howto_action = QAction(tr("action.examples"), self)
        howto_action.setFont(self._emoji_font)
        howto_action.triggered.connect(self.show_how_to_use)
        help_menu.addAction(howto_action)

        help_menu.addSeparator()

        webapp_action = QAction(tr("action.webapp"), self)
        webapp_action.setFont(self._emoji_font)
        webapp_action.triggered.connect(lambda: self._open_url(WEBAPP_URL))
        help_menu.addAction(webapp_action)

        feedback_action = QAction(tr("action.feedback"), self)
        feedback_action.setFont(self._emoji_font)
        feedback_action.triggered.connect(lambda: self._open_url(ISSUES_URL))
        help_menu.addAction(feedback_action)

        # Quick links
        quick_links = QHBoxLayout()
        quick_links.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        vbox.addLayout(quick_links)

        webapp_btn = QPushButton(tr("button.webapp"))
        webapp_btn.setFont(self._emoji_font)
        webapp_btn.clicked.connect(lambda: self._open_url(WEBAPP_URL))
        quick_links.addWidget(webapp_btn)

        howto_btn = QPushButton(tr("button.examples"))
        howto_btn.setFont(self._emoji_font)
        howto_btn.clicked.connect(self.show_how_to_use)
        quick_links.addWidget(howto_btn)

        feedback_btn = QPushButton(tr("button.feedback"))
        feedback_btn.setFont(self._emoji_font)
        feedback_btn.clicked.connect(lambda: self._open_url(ISSUES_URL))
        quick_links.addWidget(feedback_btn)

        vbox.addSpacing(8)

        # DOI entry
        entry_box = QHBoxLayout()
        vbox.addLayout(entry_box)

        label = QLabel(tr("label.doi"))
        entry_box.addWidget(label)

        self.doi_entry = QLineEdit()
        self.doi_entry.setPlaceholderText(tr("placeholder.query"))
        entry_box.addWidget(self.doi_entry)
        # Trigger fetch when user presses Enter in the DOI entry
        self.doi_entry.returnPressed.connect(self.fetch_bibtex)

        fetch_btn = QPushButton(tr("button.fetch"))
        fetch_btn.clicked.connect(self.fetch_bibtex)
        entry_box.addWidget(fetch_btn)

        # Status label
        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.status.setTextFormat(Qt.TextFormat.RichText)
        vbox.addWidget(self.status)

        # Text view
        self.textview = QTextEdit()
        self.textview.setReadOnly(True)
        self.textview.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.textview.setMinimumHeight(250)
        vbox.addWidget(self.textview)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        vbox.addLayout(btn_box)

        copy_btn = QPushButton(tr("button.copy_clipboard"))
        copy_btn.setFont(self._emoji_font)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_box.addWidget(copy_btn)

        # Keep references to worker/thread so they don't get GC'd
        self._worker_thread = None

    def _setup_emoji_font(self):
        """Set up a font with good emoji support across different desktop environments."""
        # Emoji font families with fallbacks (order matters)
        emoji_fonts = [
            "Noto Color Emoji",  # Best cross-platform emoji support
            "Noto Emoji",
            "Apple Color Emoji",  # macOS
            "Segoe UI Emoji",  # Windows
            "DejaVu Sans",  # Good Linux support
        ]
        
        # Get the system default font and preserve its size
        default_font = QFont()
        font_size = default_font.pointSize()
        
        font = QFont()
        font.setPointSize(font_size)
        
        # Try to set the font family with fallbacks
        font.setFamilies(emoji_fonts)
        return font

    def _format_status_with_emoji(self, text: str) -> str:
        """Format status text with emoji characters using emoji font."""
        # Find emoji characters and wrap them in HTML with emoji font
        emoji_list = "✅📋🌐💬ℹ️"
        emoji_font_families = "Noto Color Emoji, Noto Emoji, Apple Color Emoji, Segoe UI Emoji, DejaVu Sans"
        
        result = text
        for emoji in emoji_list:
            if emoji in result:
                result = result.replace(
                    emoji,
                    f'<span style="font-family: {emoji_font_families}">{emoji}</span>'
                )
        return result

    def _open_url(self, url: str) -> None:
        """Open an external URL in the user's default browser."""
        try:
            QDesktopServices.openUrl(QUrl(url))
        except Exception:
            self.status.setText(self._format_status_with_emoji(tr("status.link_open_failed")))

    def show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def show_how_to_use(self):
        dlg = HowToUseDialog(self)
        dlg.exec()

    def fetch_bibtex(self):
        doi = self.doi_entry.text().strip()
        if not doi:
            self.status.setText(self._format_status_with_emoji(tr("status.enter_valid_doi")))
            return

        self.status.setText(tr("status.fetching"))
        self.textview.clear()

        worker = FetchWorker(doi)

        def thread_target():
            worker.run()

        worker.finished.connect(self.on_fetch_finished)

        t = threading.Thread(target=thread_target, daemon=True)
        t.start()

        self._worker_thread = (worker, t)

    def on_fetch_finished(self, found: bool, bibtex: str, error: object):
        if found:
            self.textview.setPlainText(bibtex)
            self.status.setText(self._format_status_with_emoji(tr("status.fetch_success")))
        else:
            self.textview.clear()
            if error:
                self.status.setText(self._format_status_with_emoji(tr("status.error", error=error)))
            else:
                self.status.setText(self._format_status_with_emoji(tr("status.error_not_found")))

        self._worker_thread = None

    def copy_to_clipboard(self):
        text = self.textview.toPlainText()
        if text.strip():
            ok = copy_to_clipboard(text)
            if ok:
                self.status.setText(self._format_status_with_emoji(tr("status.copy_success")))
            else:
                self.status.setText(self._format_status_with_emoji(tr("status.copy_failed")))
        else:
            self.status.setText(self._format_status_with_emoji(tr("status.nothing_to_copy")))
