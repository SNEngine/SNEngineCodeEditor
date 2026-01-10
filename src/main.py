# main.py
import sys
import os
import traceback
import logging
from datetime import datetime

# Set up logging to redirect print statements to a log file
def setup_logging():
    # Create logs directory if it doesn't exist
    # In PyInstaller, we need to handle the path differently
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        application_path = os.path.dirname(sys.executable)
    else:
        # Running in normal Python environment
        application_path = os.path.dirname(os.path.abspath(__file__))

    logs_dir = os.path.join(application_path, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Create log filename with timestamp
    log_filename = os.path.join(logs_dir, f"application_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # Also keep printing to console
        ]
    )

    # Redirect stdout to log
    class LoggerWriter:
        def __init__(self, level):
            self.level = level
            self.linebuf = ''

        def write(self, buf):
            # Check if sys.stdout is still available to prevent errors in PyInstaller
            if sys.stdout is None:
                return
            temp_linebuf = self.linebuf + buf
            self.linebuf = ''
            for line in temp_linebuf.splitlines(True):
                if line[-1] == '\n':
                    logging.log(self.level, line.rstrip())
                else:
                    self.linebuf = line

        def flush(self):
            if self.linebuf != '':
                logging.log(self.level, self.linebuf.rstrip())
            self.linebuf = ''

    # Replace stdout and stderr with our logger, but only if not in PyInstaller frozen environment
    # In PyInstaller, sys.stdout might be None which causes issues
    if not getattr(sys, 'frozen', False):
        sys.stdout = LoggerWriter(logging.INFO)
        sys.stderr = LoggerWriter(logging.ERROR)

# Call setup_logging before other imports to catch early print statements
setup_logging()

# Import PyQt5 first
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

# Add the src directory to the path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from view import SNILEditorWindow

# Import GPU debug utility and print debug info
try:
    from gpu_debug import print_gpu_debug_info
    print_gpu_debug_info()
except ImportError:
    print("GPU Debug utility not available")

def main():
    # 1. QApplication initialization
    app = QApplication(sys.argv)

    # 2. Create and show splash screen
    splash_pix = None
    splash = None

    # Look for splash image in various locations
    splash_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'splash.png'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'promo.png'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'splash.png'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', 'splash.png'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'splash.png'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'promo.png')
    ]

    for path in splash_paths:
        if os.path.exists(path):
            splash_pix = QPixmap(path)
            break

    # Show splash screen if image found
    if splash_pix and not splash_pix.isNull():
        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        splash.show()
        app.processEvents()  # Allow the splash screen to be displayed

    # 3. Create and display the main window
    try:
        editor_window = SNILEditorWindow()
        editor_window.show()
        print("Window created successfully. Starting event loop...")
    except Exception as e:
        print("Error creating window:")
        traceback.print_exc()
        if splash:
            splash.finish(editor_window)  # Close splash if it was shown
        return

    # 4. Close splash screen if it was shown
    if splash:
        splash.finish(editor_window)

    # 5. Start the main event loop
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()