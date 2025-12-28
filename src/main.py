# main.py
import sys
import os
import traceback

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