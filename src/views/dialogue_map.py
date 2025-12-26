"""
Dialogue Map functionality for SNIL Editor
Extracts dialogue names from code and displays them in a visual map
"""
import re
from typing import List, Dict, Tuple
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor


class DialogueMapPanel(QWidget):
    """Panel that displays a map of dialogues found in the current file"""

    # Signal emitted when a dialogue is clicked
    dialogue_clicked = pyqtSignal(int)  # line_number

    def __init__(self, parent=None, styles=None):
        super().__init__(parent)
        self.dialogues = []  # List of (line_number, name) tuples
        self.is_collapsed = False
        self.main_splitter = None  # Will be set by the main window
        self.expanded_size = 250  # Default expanded size
        self.styles = styles or {}  # Theme styles
        self.init_ui()

    def init_ui(self):
        """Initialize the UI for the dialogue map panel"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Create a title bar with toggle button
        title_bar_layout = QHBoxLayout()

        # Title
        self.title_label = QLabel("Dialogue Map")
        title_font = QFont()
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        title_bar_layout.addWidget(self.title_label)

        # Toggle button (arrow)
        self.toggle_button = QPushButton("◀")  # Left arrow when expanded
        self.toggle_button.setFixedSize(20, 20)
        self.toggle_button.clicked.connect(self.toggle_panel)
        title_bar_layout.addWidget(self.toggle_button)

        layout.addLayout(title_bar_layout)

        # Scroll area for dialogue buttons
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Container for dialogue buttons
        self.dialogue_container = QWidget()
        self.dialogue_layout = QVBoxLayout(self.dialogue_container)
        self.dialogue_layout.setAlignment(Qt.AlignTop)
        self.dialogue_layout.setSpacing(3)

        self.scroll_area.setWidget(self.dialogue_container)
        layout.addWidget(self.scroll_area)

    def toggle_panel(self):
        """Toggle the visibility of the dialogue map panel"""
        if hasattr(self, 'main_window'):
            self.main_window.toggle_dialogue_map()
        
    def extract_dialogues(self, text: str) -> List[Tuple[int, str]]:
        """
        Extract dialogue names from the given text.
        Looks for patterns like 'name: DialogueName' in the text.
        Returns a list of (line_number, dialogue_name) tuples.
        """
        dialogues = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, start=1):
            # Look for 'name: <dialogue_name>' pattern (case-insensitive)
            match = re.match(r'^\s*name\s*:\s*(.+)', line, re.IGNORECASE)
            if match:
                dialogue_name = match.group(1).strip()
                dialogues.append((line_num, dialogue_name))
        
        return dialogues
    
    def update_dialogue_map(self, text: str):
        """Update the dialogue map based on the provided text"""
        # Clear existing dialogue buttons
        self.clear_dialogue_buttons()
        
        # Extract dialogues from the text
        self.dialogues = self.extract_dialogues(text)
        
        # Create buttons for each dialogue
        for line_num, dialogue_name in self.dialogues:
            button = QPushButton(f"{dialogue_name}")
            button.setToolTip(f"Click to go to line {line_num}")
            # Use a default parameter to capture the current value of line_num
            button.clicked.connect(lambda checked=False, ln=line_num: self.dialogue_clicked.emit(ln))
            
            # Apply styling from theme if available, otherwise use defaults
            if hasattr(self, 'styles') and self.styles:
                theme = self.styles.get('DarkTheme', {})
                bg_color = theme.get('DialogueMapBgColor', '#3A3A3A')
                border_color = theme.get('DialogueMapBorderColor', '#5A5A5A')
                hover_bg = theme.get('DialogueMapHoverBgColor', '#4A4A4A')
                hover_border = theme.get('DialogueMapHoverBorderColor', '#6A6A6A')
                text_color = theme.get('Foreground', '#E8E8E8')
            else:
                # Default fallback colors
                bg_color = '#3A3A3A'
                border_color = '#5A5A5A'
                hover_bg = '#4A4A4A'
                hover_border = '#6A6A6A'
                text_color = '#E8E8E8'

            # Style the button to look like a dialogue blob
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    color: {text_color};
                    border: 1px solid {border_color};
                    border-radius: 8px;
                    padding: 6px 8px;  /* Increased padding */
                    text-align: left;
                    font-size: 12px;
                    margin-bottom: 4px;  /* Add space between buttons */
                }}
                QPushButton:hover {{
                    background-color: {hover_bg};
                    border: 1px solid {hover_border};
                }}
            """)

            self.dialogue_layout.addWidget(button)
    
    def clear_dialogue_buttons(self):
        """Clear all dialogue buttons from the layout"""
        while self.dialogue_layout.count():
            child = self.dialogue_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def get_dialogue_position(self, dialogue_name: str) -> int:
        """Get the line number for a specific dialogue name"""
        for line_num, name in self.dialogues:
            if name == dialogue_name:
                return line_num
        return -1

    def update_styles(self, styles):
        """Update the styles for the dialogue map panel"""
        self.styles = styles or {}
        # Reapply styles to existing dialogue buttons
        # Loop through all widgets in the layout and update their styles
        for i in range(self.dialogue_layout.count()):
            widget = self.dialogue_layout.itemAt(i).widget()
            if widget and isinstance(widget, QPushButton):
                # Apply styling from theme if available, otherwise use defaults
                theme = self.styles.get('DarkTheme', {})
                bg_color = theme.get('DialogueMapBgColor', '#3A3A3A')
                border_color = theme.get('DialogueMapBorderColor', '#5A5A5A')
                hover_bg = theme.get('DialogueMapHoverBgColor', '#4A4A4A')
                hover_border = theme.get('DialogueMapHoverBorderColor', '#6A6A6A')
                text_color = theme.get('Foreground', '#E8E8E8')

                # Style the button to look like a dialogue blob
                widget.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {bg_color};
                        color: {text_color};
                        border: 1px solid {border_color};
                        border-radius: 8px;
                        padding: 6px 8px;
                        text-align: left;
                        font-size: 12px;
                        margin-bottom: 4px;
                    }}
                    QPushButton:hover {{
                        background-color: {hover_bg};
                        border: 1px solid {hover_border};
                    }}
                """)