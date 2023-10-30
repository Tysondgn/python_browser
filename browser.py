import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEngineProfile, QWebEnginePage
import re
import requests

# Define a custom ErrorPage class that inherits from QWebEnginePage
class ErrorPage(QWebEnginePage):
    def certificateError(self, certificateError):
        # Handle certificate errors here (if needed)
        certificateError.ignore()

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # Handle JavaScript console messages here (if needed)
        pass

class AdBlockWebView(QWebEngineView):
    def __init__(self):
        super().__init__()
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299')
        self.ad_blocking_enabled = True  # Initially, ad-blocking is enabled
        self.update_ad_blocking()
        self.loadFinished.connect(self.on_page_load)

    def update_ad_blocking(self):
        settings = self.page().settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, self.ad_blocking_enabled)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, not self.ad_blocking_enabled)

    def toggle_ad_blocking(self):
        self.ad_blocking_enabled = not self.ad_blocking_enabled
        self.update_ad_blocking()
        self.reload()

    def on_page_load(self):
        if self.ad_blocking_enabled:
            # Check if ad-blocking is enabled and block ads here
            # You would need to use a proper ad-blocking library or ruleset
            pass

# class AdBlockSettingsDialog(QDialog):
class AdBlockSettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Ad-Blocking Settings")
        self.ad_block_enabled_checkbox = QCheckBox("Enable Ad-Blocking")
        self.ad_block_enabled_checkbox.setChecked(parent.browser.ad_blocking_enabled)
        self.ad_block_enabled_checkbox.stateChanged.connect(self.toggle_ad_blocking)

        layout = QVBoxLayout()
        layout.addWidget(self.ad_block_enabled_checkbox)
        self.setLayout(layout)

    def toggle_ad_blocking(self, state):
        enabled = state == Qt.Checked
        self.parent().browser.toggle_ad_blocking()  # Remove the argument here



class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.browser = AdBlockWebView()
        self.setCentralWidget(self.browser)
        self.showMaximized()
        self.setWindowIcon(QIcon('icons/icon.png'))
        self.setWindowTitle("B2B")
        self.browser.setPage(ErrorPage())  # Set custom error page handling
        self.browser.loadFinished.connect(self.on_load_finished)

        # Set the home page during initialization
        self.navigate_home()

        # Navbar
        navbar = QToolBar()
        self.addToolBar(navbar)

        back_btn_icon = QIcon('icons/back.png')
        back_btn = QAction('', self)
        back_btn.setIcon(back_btn_icon)
        back_btn.triggered.connect(self.browser.back)
        navbar.addAction(back_btn)

        forward_btn_icon = QIcon('icons/forward.png')
        forward_btn = QAction('', self)
        forward_btn.setIcon(forward_btn_icon)
        forward_btn.triggered.connect(self.browser.forward)
        navbar.addAction(forward_btn)

        reload_btn = QAction('🔄️', self)
        reload_btn.triggered.connect(self.browser.reload)
        navbar.addAction(reload_btn)

        home_btn = QAction('🏠', self)
        home_btn.triggered.connect(self.navigate_home)
        navbar.addAction(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        self.browser.urlChanged.connect(self.update_url)

        # Create icons for the ad-block button
        self.adblock_enabled_icon = QIcon('icons/adblock_enabled.png')
        self.adblock_disabled_icon = QIcon('icons/adblock_disabled.png')

        # Create a custom action for the ad-block button
        self.ad_block_btn = QAction('', self)
        self.ad_block_btn.setIcon(self.adblock_enabled_icon if self.browser.ad_blocking_enabled else self.adblock_disabled_icon)
        self.ad_block_btn.triggered.connect(self.toggle_ad_blocking)

        # Add the custom action to the toolbar as a button
        navbar.addAction(self.ad_block_btn)

         # Add a button to open ad-blocking settings
        ad_block_settings_btn = QAction('Ad-Blocking Settings', self)
        ad_block_settings_btn.triggered.connect(self.show_ad_block_settings)
        navbar.addAction(ad_block_settings_btn)

    def show_ad_block_settings(self):
        dialog = AdBlockSettingsDialog(self)
        dialog.exec()


    def toggle_ad_blocking(self):
        self.browser.toggle_ad_blocking()
        # Update the ad-block button's icon based on the new state
        self.ad_block_btn.setIcon(self.adblock_enabled_icon if self.browser.ad_blocking_enabled else self.adblock_disabled_icon)

    def navigate_home(self):
        self.browser.setUrl(QUrl('http://duckduckgo.com'))

    def navigate_to_url(self):
        url = self.url_bar.text()

        # Check if the input is a valid URL
        valid_domains = ['.com', '.org', '.net', '.gov', '.edu']  # Add more as needed
        if re.match(r'^(https?://)', url) or any(domain in url for domain in valid_domains) or not (' ' in url or '\n' in url):
            try:
                # Check if the URL is reachable
                response = requests.head(url)
                if response.status_code == 200:
                    self.browser.setUrl(QUrl(url))
                else:
                    # URL is not reachable, proceed to search
                    self.search_with_query(url)
            except requests.exceptions.RequestException:
                # An error occurred during the request, proceed to search
                self.search_with_query(url)
        else:
            # Format the input as a search query and navigate
            self.search_with_query(url)

    def search_with_query(self, query):
        search_query = '+'.join(query.split())
        search_url = f'https://www.duckduckgo.com/?q={search_query}'
        self.browser.setUrl(QUrl(search_url))

    def update_url(self, q):
        self.url_bar.setText(q.toString())

    def on_load_finished(self, success):
        if not success:
            # If the page did not load successfully, display an error page
            error_page_content = """
                <html>
                <body>
                <h1>Error Loading Page</h1>
                <p>The requested URL could not be loaded. Please check your internet connection.</p>
                </body>
                </html>
            """
            self.browser.setHtml(error_page_content)
            
            # Clear the URL bar text
            self.url_bar.clear()

app = QApplication(sys.argv)
QApplication.setApplicationName('Browser')
window = MainWindow()
window.show()
app.exec_()