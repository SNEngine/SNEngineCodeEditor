"""
Autocomplete popup for Jump To functionality
"""
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QFont, QColor


class AutocompletePopup(QListWidget):
    """
    A popup list widget for autocomplete suggestions.
    Shows a list of available dialog names when typing 'Jump To'.
    """
    item_selected = pyqtSignal(str)  # Signal emitted when an item is selected

    def __init__(self, parent=None, styles=None):
        super().__init__(parent)
        self.styles = styles or {}
        
        # Configure the popup - use Qt.ToolTip to avoid blocking input
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFrameStyle(QFrame.NoFrame)
        self.setWindowOpacity(0.95)

        # Set focus policy to avoid blocking input
        self.setFocusPolicy(Qt.NoFocus)

        # Set up appearance based on styles
        self._setup_appearance()

        # Connect item selection
        self.itemClicked.connect(self._on_item_clicked)

        # Set initial visibility to hidden
        self.hide()

    def _setup_appearance(self):
        """Set up the appearance based on styles."""
        theme = self.styles.get('DarkTheme', {}) if self.styles else {}
        
        # Set background color
        bg_color = theme.get('SecondaryBackground', '#2A2A2A')
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {bg_color};
                border: 1px solid {theme.get('BorderColor', '#3A3A3A')};
                border-radius: 4px;
                padding: 2px;
            }}
            QListWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {theme.get('BorderColor', '#3A3A3A')};
            }}
            QListWidget::item:selected {{
                background-color: {theme.get('HoverColor', '#3A3A3A')};
                color: {theme.get('HighlightColor', '#C84B31')};
            }}
            QListWidget::item:hover {{
                background-color: {theme.get('HoverColor', '#3A3A3A')};
            }}
        """)
        
        # Set font
        font = QFont()
        font.setFamily("Consolas, 'Courier New', monospace")
        font.setPointSize(10)
        self.setFont(font)

    def update_items(self, items):
        """Update the list of items in the popup."""
        self.clear()
        for item_text in items:
            item = QListWidgetItem(item_text)
            item.setFlags(item.flags() | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.addItem(item)
        
        # Select the first item if available
        if self.count() > 0:
            self.setCurrentRow(0)

    def show_popup(self, position):
        """Show the popup at the specified position."""
        if self.count() > 0:
            # Calculate the height based on the number of items
            # Each item typically has a height of about 25-30 pixels
            item_height = 30  # Approximate height per item
            max_visible_items = 10  # Maximum number of items to show without scrolling
            num_items = min(self.count(), max_visible_items)
            calculated_height = num_items * item_height + 10  # Add some padding

            # Set the maximum height to show scrollbars if needed
            self.setMaximumHeight(calculated_height)

            # Adjust size to fit content
            self.adjustSize()

            # Position the popup below the cursor position
            popup_rect = QRect(position, self.sizeHint())
            screen_rect = self.screen().availableGeometry()

            # Adjust position to stay within screen bounds
            if popup_rect.bottom() > screen_rect.bottom():
                popup_rect.moveTop(position.y() - popup_rect.height())
            if popup_rect.right() > screen_rect.right():
                popup_rect.moveLeft(screen_rect.right() - popup_rect.width())

            self.setGeometry(popup_rect)
            self.show()
            # Don't call setFocus() to avoid blocking input in the editor

    def hide_popup(self):
        """Hide the popup."""
        self.hide()

    def _on_item_clicked(self, item):
        """Handle item click event."""
        self.item_selected.emit(item.text())
        self.hide()

    def keyPressEvent(self, event):
        """Handle keyboard events for navigation."""
        if event.key() == Qt.Key_Up:
            current_row = self.currentRow()
            if current_row > 0:
                self.setCurrentRow(current_row - 1)
            else:
                self.setCurrentRow(self.count() - 1)
        elif event.key() == Qt.Key_Down:
            current_row = self.currentRow()
            if current_row < self.count() - 1:
                self.setCurrentRow(current_row + 1)
            else:
                self.setCurrentRow(0)
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            current_item = self.currentItem()
            if current_item:
                self.item_selected.emit(current_item.text())
                self.hide()
        elif event.key() == Qt.Key_Escape:
            self.hide()
        else:
            # For other keys, pass to parent
            super().keyPressEvent(event)
            return
        event.accept()