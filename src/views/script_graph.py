import re
import math
import sys
import os
from typing import List, Dict, Tuple
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMainWindow
from PyQt5.QtCore import Qt, QPointF, QRectF, QRect, QSize, QByteArray
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QTransform, QFontMetrics, QIcon, QPixmap
from PyQt5.QtSvg import QSvgRenderer

class ScriptGraphNode:
    def __init__(self, node_id: str, node_type: str, content: str, x: float = 0, y: float = 0):
        self.id = node_id
        self.type = node_type
        self.content = content
        self.x = x
        self.y = y
        self.width = 260.0
        self.height = 90.0
        self.hdr_h = 26.0

    def calculate_height(self, font_metrics: QFontMetrics):
        flags = Qt.AlignLeft | Qt.TextWordWrap | Qt.TextWrapAnywhere
        inner_width = int(self.width - 30)
        
        text_rect = font_metrics.boundingRect(
            QRect(0, 0, inner_width, 1000),
            flags,
            self.content
        )
        
        self.height = max(90.0, self.hdr_h + text_rect.height() + 40)

    def get_rect(self):
        return QRectF(self.x, self.y, self.width, self.height)

    @property
    def enter_port(self):
        return QPointF(self.x, self.y + self.height / 2.0)

    @property
    def exit_port(self):
        return QPointF(self.x + self.width, self.y + self.height / 2.0)

from PyQt5.QtWidgets import QTabWidget

class ScriptGraphWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Script Graph Visualization")
        self.setGeometry(100, 100, 1200, 700)
        self.tab_widget = None
        self.init_ui()

    def _get_resource_path(self, relative_path: str) -> str:
        """
        Gets the path to a resource.
        In EXE mode, the file structure is based on PyInstaller --add-data specification.
        """
        if getattr(sys, 'frozen', False):
            # In PyInstaller (EXE) mode
            base_path = os.path.dirname(sys.executable)

            # Check in executable directory (where --add-data puts files)
            full_path = os.path.join(base_path, relative_path)
            if os.path.exists(full_path):
                return full_path

            # Check in PyInstaller temp directory
            try:
                temp_path = sys._MEIPASS
                temp_full_path = os.path.join(temp_path, relative_path)
                if os.path.exists(temp_full_path):
                    return temp_full_path
            except AttributeError:
                # _MEIPASS not available, skip this check
                pass

            # If neither worked, default to base path
            return full_path
        else:
            # In development mode: icons are in the src folder
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up to src/
            return os.path.join(base_path, relative_path)

    def _load_graph_icon(self) -> str:
        """Loads the dialogue graph SVG icon from file, fallback to default if not found."""
        try:
            icon_path = self._get_resource_path('icons/dialogue_graph_icon.svg')
            with open(icon_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback to a simple graph-like icon if file not found
            return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <path fill="#E06C75" d="M2,2 L14,2 L14,14 L2,14 Z M4,4 L12,4 L12,12 L4,12 Z"/>
  <path fill="#C678DD" d="M6,6 L10,6 L10,8 L6,8 Z"/>
</svg>
"""

    def _create_icon_from_svg_content(self, svg_content: str) -> QIcon:
        """Creates a QIcon from SVG content using QSvgRenderer for better compatibility."""
        try:
            # Create a pixmap with the desired size
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)  # Make background transparent

            # Create a painter to draw on the pixmap
            from PyQt5.QtGui import QPainter
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

            # Create an SVG renderer and render to the painter
            svg_bytes = QByteArray(svg_content.encode('utf-8'))
            renderer = QSvgRenderer(svg_bytes)
            renderer.render(painter)

            painter.end()

            # Return QIcon from the pixmap
            return QIcon(pixmap)
        except Exception:
            # Fallback to the original method if SVG rendering fails
            svg_bytes = QByteArray(svg_content.encode('utf-8'))
            base64_data = svg_bytes.toBase64().data().decode()
            data_uri = f'data:image:svg+xml;base64,{base64_data}'
            return QIcon(data_uri)

    def closeEvent(self, event):
        """Override close event to hide the window instead of destroying it"""
        # Hide the window instead of closing it completely
        self.hide()
        # Accept the event to prevent the window from being destroyed
        event.ignore()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        warning_label = QLabel("⚠️ Approximate Unity Preview. Node logic and flow layout simulated.")
        warning_label.setStyleSheet("""
            QLabel {
                background-color: #121212;
                color: #D4AF37;
                padding: 2px 15px;
                border-bottom: 1px solid #222222;
                font-family: 'Segoe UI';
                font-size: 10px;
            }
        """)
        warning_label.setFixedHeight(22)
        layout.addWidget(warning_label)

        # Create tab widget for multiple graphs
        self.tab_widget = QTabWidget()
        # Apply dark theme styling to the tab widget
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #222222;
                background-color: #191919;
            }
            QTabBar::tab {
                background-color: #2A2A2A;
                color: #E8E8E8;
                padding: 6px 12px;
                margin: 2px;
                border: 1px solid #3A3A3A;
                border-bottom-color: #222222;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1F1F1F;
                color: #E06C75;
                border-bottom-color: #1F1F1F;
            }
            QTabBar::tab:hover {
                background-color: #3A3A3A;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)
        layout.addWidget(self.tab_widget)

    def _load_node_types_config(self):
        """Load node type configuration from JSON file."""
        import json

        try:
            config_path = self._get_resource_path('node_types_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            # Fallback to default configuration if config file not found
            return {
                "node_types": [
                    {
                        "name": "start",
                        "pattern": "^START",
                        "description": "Start of a dialogue or section"
                    },
                    {
                        "name": "end",
                        "pattern": "^END",
                        "description": "End of a dialogue or section"
                    },
                    {
                        "name": "function",
                        "pattern": "^\\s*function\\s+",
                        "description": "Function definition"
                    },
                    {
                        "name": "function_call",
                        "pattern": "^\\s*call\\s+",
                        "description": "Function call"
                    },
                    {
                        "name": "jump",
                        "pattern": "^\\s*jump\\s+to\\s+",
                        "description": "Jump to another section"
                    },
                    {
                        "name": "wait",
                        "pattern": "^\\s*wait\\s+",
                        "description": "Wait/pause in the dialogue"
                    },
                    {
                        "name": "show",
                        "pattern": "^\\s*show\\s+",
                        "description": "Show character or background"
                    }
                ],
                "default_node_type": "dialogue",
                "ignore_patterns": [
                    "^\\s*name\\s*:",
                    "^\\s*$"
                ]
            }
        except json.JSONDecodeError:
            # Fallback to default configuration if config file is invalid
            print("Warning: Invalid JSON in node_types_config.json, using default configuration")
            return {
                "node_types": [
                    {
                        "name": "start",
                        "pattern": "^START",
                        "description": "Start of a dialogue or section"
                    },
                    {
                        "name": "end",
                        "pattern": "^END",
                        "description": "End of a dialogue or section"
                    },
                    {
                        "name": "function",
                        "pattern": "^\\s*function\\s+",
                        "description": "Function definition"
                    },
                    {
                        "name": "function_call",
                        "pattern": "^\\s*call\\s+",
                        "description": "Function call"
                    },
                    {
                        "name": "jump",
                        "pattern": "^\\s*jump\\s+to\\s+",
                        "description": "Jump to another section"
                    },
                    {
                        "name": "wait",
                        "pattern": "^\\s*wait\\s+",
                        "description": "Wait/pause in the dialogue"
                    },
                    {
                        "name": "show",
                        "pattern": "^\\s*show\\s+",
                        "description": "Show character or background"
                    }
                ],
                "default_node_type": "dialogue",
                "ignore_patterns": [
                    "^\\s*name\\s*:",
                    "^\\s*$"
                ]
            }
        except Exception as e:
            # Fallback to default configuration for any other error
            print(f"Warning: Error loading node_types_config.json: {e}, using default configuration")
            return {
                "node_types": [
                    {
                        "name": "start",
                        "pattern": "^START",
                        "description": "Start of a dialogue or section"
                    },
                    {
                        "name": "end",
                        "pattern": "^END",
                        "description": "End of a dialogue or section"
                    },
                    {
                        "name": "function",
                        "pattern": "^\\s*function\\s+",
                        "description": "Function definition"
                    },
                    {
                        "name": "function_call",
                        "pattern": "^\\s*call\\s+",
                        "description": "Function call"
                    },
                    {
                        "name": "jump",
                        "pattern": "^\\s*jump\\s+to\\s+",
                        "description": "Jump to another section"
                    },
                    {
                        "name": "wait",
                        "pattern": "^\\s*wait\\s+",
                        "description": "Wait/pause in the dialogue"
                    },
                    {
                        "name": "show",
                        "pattern": "^\\s*show\\s+",
                        "description": "Show character or background"
                    },
                    {
                        "name": "condition",
                        "pattern": "^\\s*if\\s+.*",
                        "description": "Conditional statement"
                    }
                ],
                "default_node_type": "dialogue",
                "ignore_patterns": [
                    "^\\s*name\\s*:",
                    "^\\s*$"
                ]
            }

    def parse_script_content(self, content: str):
        sections = content.split('\n---\n')

        # Clear existing tabs
        self.tab_widget.clear()

        # Load the graph icon once for all tabs
        graph_svg_content = self._load_graph_icon()
        graph_icon = self._create_icon_from_svg_content(graph_svg_content)

        # Load node types configuration
        node_types_config = self._load_node_types_config()
        node_types = node_types_config.get("node_types", [])
        default_node_type = node_types_config.get("default_node_type", "dialogue")
        ignore_patterns = node_types_config.get("ignore_patterns", [])

        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            # Extract the name of the dialogue/section
            name_match = re.search(r'^name:\s*(.+)', section, re.MULTILINE | re.IGNORECASE)
            section_name = name_match.group(1).strip() if name_match else f"Section {i+1}"

            # Create a new canvas for this section
            graph_canvas = ScriptGraphCanvas()

            # Parse nodes and connections for this section only
            lines = section.split('\n')
            nodes = []
            connections = []
            node_id_counter = 0
            prev_node = None

            # Track conditional blocks for proper branching
            conditional_stack = []  # Stack to track conditional blocks (if_node, endif_pos)
            current_conditional = None  # Current conditional being processed (if_node, true_branch_started, false_branch_started)

            # Preprocess to identify conditional structures
            processed_lines = []
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # Check if this is a conditional start
                if re.match(r'^\s*if\s+.*', line, re.IGNORECASE) or 'If Show Variant' in line:
                    # Collect the entire conditional block
                    conditional_block = [line]
                    i += 1
                    while i < len(lines):
                        next_line = lines[i].strip()
                        if next_line.lower() == 'endif':
                            conditional_block.append(next_line)
                            i += 1
                            break
                        else:
                            conditional_block.append(next_line)
                            i += 1
                    processed_lines.append(('conditional', conditional_block))
                else:
                    processed_lines.append(('normal', [line]))
                    i += 1

            # Track the last nodes from conditional blocks to connect to the next statement
            conditional_end_nodes = []  # Nodes that need to connect to the next statement after conditionals

            # Process the parsed lines to create nodes and connections
            for item_idx, item in enumerate(processed_lines):
                item_type, item_lines = item

                if item_type == 'conditional':
                    # Handle conditional block
                    conditional_nodes, conditional_connections, last_true_node, last_false_node = self._parse_conditional_block(
                        item_lines, node_id_counter, nodes, node_types, default_node_type, ignore_patterns
                    )

                    # Add the conditional nodes to the main nodes list
                    nodes.extend(conditional_nodes)

                    # Add connections from the conditional structure
                    connections.extend(conditional_connections)

                    # Update the node_id_counter to account for new nodes
                    node_id_counter += len(conditional_nodes)

                    # Connect to the first node of the conditional block if there was a previous node
                    if prev_node and conditional_nodes:
                        connections.append((prev_node.id, conditional_nodes[0].id))  # condition_node is first

                    # Store the end nodes of conditional branches for connection to next statement
                    end_nodes = []
                    if last_true_node:
                        end_nodes.append(last_true_node)
                    if last_false_node:
                        end_nodes.append(last_false_node)
                    if end_nodes:
                        conditional_end_nodes.extend(end_nodes)

                    # For conditionals, we don't set prev_node to a single node since there are two possible end points
                    # Instead, we store the end nodes to connect to the next statement when it comes
                    prev_node = None  # Reset prev_node since conditional branches don't have a single end
                else:
                    # Handle normal lines
                    for line in item_lines:
                        line = line.strip()

                        # Check if line should be ignored based on ignore patterns
                        should_ignore = False
                        for pattern in ignore_patterns:
                            if re.match(pattern, line, re.IGNORECASE):
                                should_ignore = True
                                break

                        if should_ignore:
                            continue

                        # Determine node type based on configuration
                        node_type = default_node_type
                        for node_config in node_types:
                            pattern = node_config.get("pattern", "")
                            if re.match(pattern, line, re.IGNORECASE):
                                node_type = node_config.get("name", default_node_type)
                                # Map function_call to function to maintain original behavior
                                if node_type == "function_call":
                                    node_type = "function"
                                break  # First match wins

                        node = ScriptGraphNode(f"n_{node_id_counter}", node_type, line)
                        nodes.append(node)

                        # Connect all conditional end nodes to this new node
                        for cond_end_node in conditional_end_nodes:
                            connections.append((cond_end_node.id, node.id))

                        # Connect to the previous node (if it wasn't from a conditional and no conditional end nodes exist)
                        if prev_node and not conditional_end_nodes:
                            connections.append((prev_node.id, node.id))

                        # Clear conditional end nodes since they've been connected
                        conditional_end_nodes = []

                        # Update prev_node for the next iteration (this will be used if there's no conditional after this node)
                        prev_node = node
                        node_id_counter += 1

            # Set the data for this canvas
            graph_canvas.set_data(nodes, connections)

            # Add the canvas to a new tab with the graph icon
            self.tab_widget.addTab(graph_canvas, graph_icon, section_name)

    def _parse_conditional_block(self, lines, start_id, existing_nodes, node_types, default_node_type, ignore_patterns):
        """
        Parse a conditional block and return nodes and connections that represent the conditional flow.
        """
        nodes = []
        connections = []
        node_id_counter = start_id

        # The first line should be the condition
        if not lines:
            return nodes, connections, None, None

        condition_line = lines[0].strip()

        # Create the condition node
        condition_node = ScriptGraphNode(f"n_{node_id_counter}", "condition", condition_line)
        nodes.append(condition_node)
        condition_node_id = condition_node.id
        node_id_counter += 1

        # Parse the conditional block content to identify True/False branches
        i = 1
        true_block = []
        false_block = []
        current_block = None

        while i < len(lines):
            line = lines[i].strip()

            if line.lower() == 'true:':
                current_block = true_block
            elif line.lower() == 'false:':
                current_block = false_block
            elif line.lower() == 'endif':
                # End of conditional block
                break
            elif current_block is not None:
                # Add to the current block
                current_block.append(line)
            else:
                # Lines before True/False (like Variants:) go to both branches or are part of the condition
                if line.lower().startswith('variants:'):
                    # Variants info - we'll include it in the condition node content
                    condition_node.content += f"\n{line}"
                elif line.strip() and not line.lower().startswith('option'):
                    # Other lines before True/False that are not option lines
                    # For now, we'll ignore these unless they're part of the variants list
                    pass
                elif line.strip().lower().startswith('option'):
                    # Option lines should be part of the condition node content
                    condition_node.content += f"\n{line}"

            i += 1

        # Process True branch
        true_nodes = []
        if true_block:
            for line in true_block:
                if line.strip():
                    # Determine node type for true branch
                    node_type = default_node_type
                    for node_config in node_types:
                        pattern = node_config.get("pattern", "")
                        if re.match(pattern, line, re.IGNORECASE):
                            node_type = node_config.get("name", default_node_type)
                            # Map function_call to function to maintain original behavior
                            if node_type == "function_call":
                                node_type = "function"
                            break  # First match wins

                    node = ScriptGraphNode(f"n_{node_id_counter}", node_type, line)
                    true_nodes.append(node)
                    node_id_counter += 1

        # Process False branch
        false_nodes = []
        if false_block:
            for line in false_block:
                if line.strip():
                    # Determine node type for false branch
                    node_type = default_node_type
                    for node_config in node_types:
                        pattern = node_config.get("pattern", "")
                        if re.match(pattern, line, re.IGNORECASE):
                            node_type = node_config.get("name", default_node_type)
                            # Map function_call to function to maintain original behavior
                            if node_type == "function_call":
                                node_type = "function"
                            break  # First match wins

                    node = ScriptGraphNode(f"n_{node_id_counter}", node_type, line)
                    false_nodes.append(node)
                    node_id_counter += 1

        # Add all nodes to the main list
        nodes.extend(true_nodes)
        nodes.extend(false_nodes)

        # Create connections:
        # 1. Condition node connects to first node in True branch
        # 2. Condition node connects to first node in False branch
        # 3. Connect nodes within each branch sequentially

        # Connect condition to true branch
        if true_nodes:
            connections.append((condition_node_id, true_nodes[0].id))
            # Connect nodes within true branch
            for j in range(len(true_nodes) - 1):
                connections.append((true_nodes[j].id, true_nodes[j + 1].id))
        else:
            # If there's no true branch content, connect directly to endif (which doesn't exist as a node)
            # In this case, we don't create a specific connection since the branch is empty
            pass

        # Connect condition to false branch
        if false_nodes:
            connections.append((condition_node_id, false_nodes[0].id))
            # Connect nodes within false branch
            for j in range(len(false_nodes) - 1):
                connections.append((false_nodes[j].id, false_nodes[j + 1].id))
        else:
            # If there's no false branch content, connect directly to endif (which doesn't exist as a node)
            # In this case, we don't create a specific connection since the branch is empty
            pass

        # Determine the last node in each branch for potential convergence
        last_true_node = true_nodes[-1] if true_nodes else None
        last_false_node = false_nodes[-1] if false_nodes else None

        return nodes, connections, last_true_node, last_false_node

class ScriptGraphCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.nodes: List[ScriptGraphNode] = []
        self.connections: List[Tuple[str, str]] = []
        self.zoom = 1.0
        self.offset = QPointF(0, 0)
        self.last_mouse_pos = QPointF()
        self.dragging_canvas = False

        # Load color configuration from JSON
        self._load_color_config()

    def _get_resource_path(self, relative_path: str) -> str:
        """
        Gets the path to a resource.
        In EXE mode, the file structure is based on PyInstaller --add-data specification.
        """
        if getattr(sys, 'frozen', False):
            # In PyInstaller (EXE) mode
            base_path = os.path.dirname(sys.executable)

            # Check in executable directory (where --add-data puts files)
            full_path = os.path.join(base_path, relative_path)
            if os.path.exists(full_path):
                return full_path

            # Check in PyInstaller temp directory
            try:
                temp_path = sys._MEIPASS
                temp_full_path = os.path.join(temp_path, relative_path)
                if os.path.exists(temp_full_path):
                    return temp_full_path
            except AttributeError:
                # _MEIPASS not available, skip this check
                pass

            # If neither worked, default to base path
            return full_path
        else:
            # In development mode: icons are in the src folder
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up to src/
            return os.path.join(base_path, relative_path)

    def _load_color_config(self):
        """Load color configuration from JSON file."""
        import json

        try:
            config_path = self._get_resource_path('graph_colors.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Load canvas colors
            canvas_colors = config.get('canvas_colors', {})
            self.color_bg = QColor(canvas_colors.get('background', '#191919'))
            self.color_grid_main = QColor(canvas_colors.get('grid_main', '#0F0F0F'))
            self.color_grid_sub = QColor(canvas_colors.get('grid_sub', '#232323'))
            self.color_link = QColor(canvas_colors.get('link', '#00FF80'))

            # Load node type colors
            node_colors = config.get('node_colors', {})
            self.type_colors = {
                'start': QColor(node_colors.get('start', '#2E682E')),
                'end': QColor(node_colors.get('end', '#682E2E')),
                'dialogue': QColor(node_colors.get('dialogue', '#2E4468')),
                'function': QColor(node_colors.get('function', '#68682E')),
                'jump': QColor(node_colors.get('jump', '#562E68')),
                'wait': QColor(node_colors.get('wait', '#464646')),
                'show': QColor(node_colors.get('show', '#684C20')),
                'condition': QColor(node_colors.get('condition', '#804080'))
            }

        except FileNotFoundError:
            # Fallback to default colors if config file not found
            self.color_bg = QColor(25, 25, 25)
            self.color_grid_main = QColor(15, 15, 15)
            self.color_grid_sub = QColor(35, 35, 35)
            self.color_link = QColor(0, 255, 128)

            self.type_colors = {
                'start': QColor(46, 104, 46), 'end': QColor(104, 46, 46),
                'dialogue': QColor(46, 68, 104), 'function': QColor(104, 104, 46),
                'jump': QColor(86, 46, 104), 'wait': QColor(70, 70, 70),
                'show': QColor(104, 76, 32), 'condition': QColor(128, 64, 128)
            }
        except json.JSONDecodeError:
            # Fallback to default colors if config file is invalid
            print("Warning: Invalid JSON in graph_colors.json, using default colors")
            self.color_bg = QColor(25, 25, 25)
            self.color_grid_main = QColor(15, 15, 15)
            self.color_grid_sub = QColor(35, 35, 35)
            self.color_link = QColor(0, 255, 128)

            self.type_colors = {
                'start': QColor(46, 104, 46), 'end': QColor(104, 46, 46),
                'dialogue': QColor(46, 68, 104), 'function': QColor(104, 104, 46),
                'jump': QColor(86, 46, 104), 'wait': QColor(70, 70, 70),
                'show': QColor(104, 76, 32), 'condition': QColor(128, 64, 128)
            }
        except Exception as e:
            # Fallback to default colors for any other error
            print(f"Warning: Error loading graph_colors.json: {e}, using default colors")
            self.color_bg = QColor(25, 25, 25)
            self.color_grid_main = QColor(15, 15, 15)
            self.color_grid_sub = QColor(35, 35, 35)
            self.color_link = QColor(0, 255, 128)

            self.type_colors = {
                'start': QColor(46, 104, 46), 'end': QColor(104, 46, 46),
                'dialogue': QColor(46, 68, 104), 'function': QColor(104, 104, 46),
                'jump': QColor(86, 46, 104), 'wait': QColor(70, 70, 70),
                'show': QColor(104, 76, 32), 'condition': QColor(128, 64, 128)
            }

    def set_data(self, nodes, connections):
        metrics = QFontMetrics(QFont("Consolas", 10))
        for node in nodes:
            node.calculate_height(metrics)
            
        self.nodes = nodes
        self.connections = connections
        self._arrange_horizontal()
        self.update()

    def _arrange_horizontal(self):
        x, y = 100.0, 300.0
        spacing = 100.0
        for node in self.nodes:
            node.x = x
            node.y = y - (node.height / 2.0)
            x += node.width + spacing

    def get_transform(self):
        t = QTransform()
        t.translate(self.width()/2, self.height()/2)
        t.scale(self.zoom, self.zoom)
        t.translate(-self.width()/2 + self.offset.x(), -self.height()/2 + self.offset.y())
        return t

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.zoom = max(0.1, min(3.0, self.zoom * (1.1 if delta > 0 else 0.9)))
        self.update()

    def mousePressEvent(self, event):
        self.dragging_canvas = True
        self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.dragging_canvas:
            self.offset += (QPointF(event.pos()) - self.last_mouse_pos) / self.zoom
            self.last_mouse_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        self.dragging_canvas = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        transform = self.get_transform()
        self._draw_grid(painter, transform)
        
        painter.setTransform(transform)
        for from_id, to_id in self.connections:
            self._draw_link(painter, from_id, to_id)
        for node in self.nodes:
            self._draw_node(painter, node)

    def _draw_grid(self, painter, transform):
        painter.fillRect(self.rect(), self.color_bg)
        inv_t, _ = transform.inverted()
        visible = inv_t.mapRect(QRectF(self.rect()))
        step = 25.0
        painter.setTransform(transform)
        
        for x in range(int(visible.left() // step * step), int(visible.right() + step), int(step)):
            painter.setPen(QPen(self.color_grid_main if x % 125 == 0 else self.color_grid_sub, 1.0))
            painter.drawLine(QPointF(x, visible.top()), QPointF(x, visible.bottom()))
        for y in range(int(visible.top() // step * step), int(visible.bottom() + step), int(step)):
            painter.setPen(QPen(self.color_grid_main if y % 125 == 0 else self.color_grid_sub, 1.0))
            painter.drawLine(QPointF(visible.left(), y), QPointF(visible.right(), y))

    def _draw_link(self, painter, from_id, to_id):
        n1 = next((n for n in self.nodes if n.id == from_id), None)
        n2 = next((n for n in self.nodes if n.id == to_id), None)
        if n1 and n2:
            p1, p2 = n1.exit_port, n2.enter_port
            dist = max(abs(p2.x() - p1.x()) * 0.5, 50.0)
            path = QPainterPath()
            path.moveTo(p1)
            path.cubicTo(p1.x() + dist, p1.y(), p2.x() - dist, p2.y(), p2.x(), p2.y())
            painter.setPen(QPen(self.color_link, 2.2))
            painter.drawPath(path)

    def _draw_node(self, painter, node):
        base_color = self.type_colors.get(node.type, QColor(60, 60, 60))
        body_color = base_color.darker(220)
        
        painter.setPen(QPen(QColor(10, 10, 10), 1.5))
        painter.setBrush(body_color)
        painter.drawRoundedRect(node.get_rect(), 8.0, 8.0)
        
        hdr_rect = QRectF(node.x, node.y, node.width, node.hdr_h)
        painter.setPen(Qt.NoPen)
        painter.setBrush(base_color)
        painter.drawRoundedRect(hdr_rect, 8.0, 8.0)
        painter.drawRect(QRectF(node.x, node.y + node.hdr_h - 5.0, node.width, 5.0))
        
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(hdr_rect.adjusted(12, 0, -12, 0), Qt.AlignVCenter, node.type.upper())
        
        painter.setFont(QFont("Consolas", 10))
        flags = Qt.AlignLeft | Qt.TextWordWrap | Qt.TextWrapAnywhere
        content_rect = node.get_rect().adjusted(15, node.hdr_h + 12, -15, -12)
        painter.drawText(content_rect, flags, node.content)
        
        painter.setBrush(self.color_link)
        painter.setPen(QPen(QColor(0, 0, 0, 100), 1.0))
        painter.drawEllipse(node.enter_port, 5.0, 5.0)
        painter.drawEllipse(node.exit_port, 5.0, 5.0)