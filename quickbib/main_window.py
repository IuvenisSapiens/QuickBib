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
        self.setWindowTitle("QuickBib: DOI → BibTeX")
        self.resize(500, 380)

        # Set up emoji font support
        self._emoji_font = self._setup_emoji_font()

        central = QWidget()
        self.setCentralWidget(central)

        vbox = QVBoxLayout()
        central.setLayout(vbox)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        quit_action = QAction("&Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = menubar.addMenu("&Edit")
        copy_action = QAction("&Copy BibTeX", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy_to_clipboard)
        edit_menu.addAction(copy_action)

        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About QuickBib", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        howto_action = QAction("How to &use", self)
        howto_action.triggered.connect(self.show_how_to_use)
        help_menu.addAction(howto_action)

        # DOI entry
        entry_box = QHBoxLayout()
        vbox.addLayout(entry_box)

        label = QLabel("DOI:")
        entry_box.addWidget(label)

        self.doi_entry = QLineEdit()
        self.doi_entry.setPlaceholderText("DOI or arXiv ID or arXiv URL or Journal URL or Article Title")
        entry_box.addWidget(self.doi_entry)
        # Trigger fetch when user presses Enter in the DOI entry
        self.doi_entry.returnPressed.connect(self.fetch_bibtex)

        fetch_btn = QPushButton("Fetch")
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

        webapp_btn = QPushButton("🌐 Web App")
        webapp_btn.setFont(self._emoji_font)
        webapp_btn.clicked.connect(lambda: self._open_url(WEBAPP_URL))
        btn_box.addWidget(webapp_btn)

        btn_box.addStretch(1)

        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.setFont(self._emoji_font)
        copy_btn.setDefault(True)
        copy_btn.setStyleSheet(
            "QPushButton {"
            "  font-weight: 600;"
            "  padding: 6px 14px;"
            "  border-radius: 6px;"
            "  border: 2px solid #6b7280;"
            "  background: transparent;"
            "}"
            "QPushButton:hover {"
            "  border-color: #4b5563;"
            "}"
            "QPushButton:pressed {"
            "  border-color: #374151;"
            "}"
        )
        copy_btn.clicked.connect(self.copy_to_clipboard)
        btn_box.addWidget(copy_btn)

        btn_box.addStretch(1)

        feedback_btn = QPushButton("💬 Send Feedback")
        feedback_btn.setFont(self._emoji_font)
        feedback_btn.clicked.connect(lambda: self._open_url(ISSUES_URL))
        btn_box.addWidget(feedback_btn)

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
            self.status.setText(self._format_status_with_emoji("ℹ️ Failed to open link."))

    def show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def show_how_to_use(self):
        dlg = HowToUseDialog(self)
        dlg.exec()

    def fetch_bibtex(self):
        doi = self.doi_entry.text().strip()
        if not doi:
            self.status.setText(self._format_status_with_emoji("ℹ️ Please enter a valid DOI. See \"Help → How to use\" for more info."))
            return

        self.status.setText("Fetching BibTeX...")
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
            self.status.setText(self._format_status_with_emoji("✅ Fetched successfully."))
        else:
            self.textview.clear()
            if error:
                self.status.setText(self._format_status_with_emoji(f"ℹ️ Error: {error}"))
            else:
                self.status.setText(self._format_status_with_emoji("ℹ️ Error: DOI not found or CrossRef request failed."))

        self._worker_thread = None

    def copy_to_clipboard(self):
        text = self.textview.toPlainText()
        if text.strip():
            ok = copy_to_clipboard(text)
            if ok:
                self.status.setText(self._format_status_with_emoji("✅ Copied to clipboard!"))
            else:
                self.status.setText(self._format_status_with_emoji("ℹ️ Failed to copy to clipboard."))
        else:
            self.status.setText(self._format_status_with_emoji("ℹ️ Nothing to copy."))
