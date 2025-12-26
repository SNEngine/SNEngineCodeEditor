import re
import math
import sys
import os
from typing import List, Dict, Tuple
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QMainWindow, QTabWidget
from PyQt5.QtCore import Qt, QPointF, QRectF, QRect, QSize, QByteArray
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QPainterPath, QTransform, QFontMetrics, QIcon, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from .node_renderer_factory import NodeRendererFactory

class ScriptGraphNode:
    def __init__(self, node_id: str, node_type: str, content: str, x: float = 0, y: float = 0):
        self.id = node_id
        self.type = node_type
        self.content = content
        self.x = x
        self.y = y
        self.width = 260.0
        self.height = 90.0
        self.hdr_h = 32.0

    def calculate_height(self, font_metrics: QFontMetrics):
        flags = Qt.AlignLeft | Qt.TextWordWrap | Qt.TextWrapAnywhere
        inner_width = int(self.width - 30)
        
        text_rect = font_metrics.boundingRect(
            QRect(0, 0, inner_width, 1000),
            flags,
            self.content
        )
        
        if "variant" in self.type.lower() or "variant" in self.content.lower():
            self.height = max(160.0, self.hdr_h + text_rect.height() + 80)
        else:
            self.height = max(90.0, self.hdr_h + text_rect.height() + 40)

    def get_rect(self):
        return QRectF(self.x, self.y, self.width, self.height)

    @property
    def enter_port(self):
        # For horizontal layout, always use left side
        return QPointF(self.x, self.y + self.height / 2.0)

    @property
    def exit_port(self):
        # For horizontal layout, always use right side
        return QPointF(self.x + self.width, self.y + self.height / 2.0)

    def get_true_port(self):
        """Get the port position for True branch output (for visualization only)"""
        return QPointF(self.x + self.width, self.y + self.height / 3)

    def get_false_port(self):
        """Get the port position for False branch output (for visualization only)"""
        return QPointF(self.x + self.width, self.y + 2 * self.height / 3)

class ScriptGraphWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Script Graph Visualization")
        self.setGeometry(100, 100, 1200, 700)
        self.tab_widget = None
        self.init_ui()

    def _get_resource_path(self, relative_path: str) -> str:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            full_path = os.path.join(base_path, relative_path)
            if os.path.exists(full_path):
                return full_path
            try:
                temp_path = sys._MEIPASS
                temp_full_path = os.path.join(temp_path, relative_path)
                if os.path.exists(temp_full_path):
                    return temp_full_path
            except AttributeError:
                pass
            return full_path
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, relative_path)

    def _load_graph_icon(self) -> str:
        try:
            icon_path = self._get_resource_path('icons/dialogue_graph_icon.svg')
            with open(icon_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return f"""
<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
  <path fill="#E06C75" d="M2,2 L14,2 L14,14 L2,14 Z M4,4 L12,4 L12,12 L4,12 Z"/>
  <path fill="#C678DD" d="M6,6 L10,6 L10,8 L6,8 Z"/>
</svg>
"""

    def _create_icon_from_svg_content(self, svg_content: str) -> QIcon:
        try:
            pixmap = QPixmap(16, 16)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            svg_bytes = QByteArray(svg_content.encode('utf-8'))
            renderer = QSvgRenderer(svg_bytes)
            renderer.render(painter)
            painter.end()
            return QIcon(pixmap)
        except Exception:
            svg_bytes = QByteArray(svg_content.encode('utf-8'))
            base64_data = svg_bytes.toBase64().data().decode()
            data_uri = f'data:image:svg+xml;base64,{base64_data}'
            return QIcon(data_uri)

    def closeEvent(self, event):
        self.hide()
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
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #222222; background-color: #191919; }
            QTabBar::tab { background-color: #2A2A2A; color: #E8E8E8; padding: 6px 12px; margin: 2px; border: 1px solid #3A3A3A; border-bottom-color: #222222; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background-color: #1F1F1F; color: #E06C75; border-bottom-color: #1F1F1F; }
            QTabBar::tab:hover { background-color: #3A3A3A; }
            QTabBar::tab:!selected { margin-top: 2px; }
        """)
        layout.addWidget(self.tab_widget)

    def _load_node_types_config(self):
        import json
        try:
            config_path = self._get_resource_path('node_types_config.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {
                "node_types": [
                    {"name": "start", "pattern": "^START"},
                    {"name": "end", "pattern": "^END"},
                    {"name": "function", "pattern": "^\\s*function\\s+"},
                    {"name": "function_call", "pattern": "^\\s*call\\s+"},
                    {"name": "jump", "pattern": "^\\s*jump\\s+to\\s+"},
                    {"name": "wait", "pattern": "^\\s*wait\\s+"},
                    {"name": "show", "pattern": "^\\s*show\\s+"},
                    {"name": "condition", "pattern": "^\\s*if\\s+.*"}
                ],
                "default_node_type": "dialogue",
                "ignore_patterns": ["^\\s*name\\s*:", "^\\s*$"]
            }

    def parse_script_content(self, content: str):
        sections = content.split('\n---\n')
        self.tab_widget.clear()
        graph_svg_content = self._load_graph_icon()
        graph_icon = self._create_icon_from_svg_content(graph_svg_content)
        node_types_config = self._load_node_types_config()
        node_types = node_types_config.get("node_types", [])
        default_node_type = node_types_config.get("default_node_type", "dialogue")
        ignore_patterns = node_types_config.get("ignore_patterns", [])

        for i, section in enumerate(sections):
            section = section.strip()
            if not section: continue
            name_match = re.search(r'^name:\s*(.+)', section, re.MULTILINE | re.IGNORECASE)
            section_name = name_match.group(1).strip() if name_match else f"Section {i+1}"
            graph_canvas = ScriptGraphCanvas()
            lines = section.split('\n')
            nodes, connections = [], []
            node_id_counter = 0
            prev_node = None
            processed_lines = []
            line_idx = 0
            while line_idx < len(lines):
                line = lines[line_idx].strip()
                if re.match(r'^\s*if\s+.*', line, re.IGNORECASE) or 'If Show Variant' in line:
                    conditional_block = [line]
                    line_idx += 1
                    while line_idx < len(lines):
                        next_line = lines[line_idx].strip()
                        conditional_block.append(next_line)
                        line_idx += 1
                        if next_line.lower() == 'endif': break
                    processed_lines.append(('conditional', conditional_block))
                else:
                    processed_lines.append(('normal', [line]))
                    line_idx += 1
            
            conditional_end_nodes = []
            for item_type, item_lines in processed_lines:
                if item_type == 'conditional':
                    c_nodes, c_conns, l_true, l_false = self._parse_conditional_block(
                        item_lines, node_id_counter, nodes, node_types, default_node_type, ignore_patterns
                    )
                    nodes.extend(c_nodes)
                    connections.extend(c_conns)
                    if prev_node and c_nodes:
                        connections.append((prev_node.id, c_nodes[0].id))
                    if l_true: conditional_end_nodes.append(l_true)
                    if l_false: conditional_end_nodes.append(l_false)
                    node_id_counter += len(c_nodes)
                    prev_node = None
                else:
                    for line in item_lines:
                        if any(re.match(p, line, re.IGNORECASE) for p in ignore_patterns): continue
                        node_type = default_node_type
                        for nc in node_types:
                            if re.match(nc.get("pattern", ""), line, re.IGNORECASE):
                                node_type = nc.get("name", default_node_type)
                                if node_type == "function_call": node_type = "function"
                                break
                        node = ScriptGraphNode(f"n_{node_id_counter}", node_type, line)
                        nodes.append(node)
                        for ce in conditional_end_nodes: connections.append((ce.id, node.id))
                        if prev_node and not conditional_end_nodes: connections.append((prev_node.id, node.id))
                        conditional_end_nodes = []
                        prev_node = node
                        node_id_counter += 1
            graph_canvas.set_data(nodes, connections)
            self.tab_widget.addTab(graph_canvas, graph_icon, section_name)

    def _parse_conditional_block(self, lines, start_id, existing_nodes, node_types, default_node_type, ignore_patterns):
        if not lines: return [], [], None, None
        node_id_counter = start_id
        condition_node = ScriptGraphNode(f"n_{node_id_counter}", "if_show_variant", lines[0].strip())
        node_id_counter += 1
        i, true_block, false_block, current_block = 1, [], [], None
        while i < len(lines):
            line = lines[i].strip()
            if line.lower() == 'true:': current_block = true_block
            elif line.lower() == 'false:': current_block = false_block
            elif line.lower() == 'endif': break
            elif current_block is not None: current_block.append(line)
            else: condition_node.content += f"\n{line}"
            i += 1
        
        def process_branch(block, counter):
            branch_nodes = []
            for line in block:
                if not line.strip(): continue
                nt = default_node_type
                for nc in node_types:
                    if re.match(nc.get("pattern", ""), line, re.IGNORECASE):
                        nt = nc.get("name", default_node_type)
                        break
                branch_nodes.append(ScriptGraphNode(f"n_{counter}", nt, line))
                counter += 1
            return branch_nodes, counter

        t_nodes, node_id_counter = process_branch(true_block, node_id_counter)
        f_nodes, node_id_counter = process_branch(false_block, node_id_counter)
        
        all_c_nodes = [condition_node] + t_nodes + f_nodes
        all_c_conns = []
        if t_nodes:
            all_c_conns.append((condition_node.id, t_nodes[0].id))
            for j in range(len(t_nodes)-1): all_c_conns.append((t_nodes[j].id, t_nodes[j+1].id))
        if f_nodes:
            all_c_conns.append((condition_node.id, f_nodes[0].id))
            for j in range(len(f_nodes)-1): all_c_conns.append((f_nodes[j].id, f_nodes[j+1].id))
            
        return all_c_nodes, all_c_conns, t_nodes[-1] if t_nodes else condition_node, f_nodes[-1] if f_nodes else condition_node

class ScriptGraphCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.nodes, self.connections = [], []
        self.zoom, self.offset = 1.0, QPointF(0, 0)
        self.last_mouse_pos, self.dragging_canvas = QPointF(), False
        self.renderer_factory = NodeRendererFactory()
        self._load_color_config()

    def _get_resource_path(self, relative_path: str) -> str:
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
            full_path = os.path.join(base_path, relative_path)
            if os.path.exists(full_path): return full_path
            try:
                temp_path = sys._MEIPASS
                return os.path.join(temp_path, relative_path)
            except AttributeError: pass
            return full_path
        else:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            return os.path.join(base_path, relative_path)

    def _load_color_config(self):
        self.color_bg = QColor(25, 25, 25)
        self.color_grid_main = QColor(15, 15, 15)
        self.color_grid_sub = QColor(35, 35, 35)
        self.color_link = QColor(0, 255, 128)
        self.type_colors = {
            'start': QColor(46, 104, 46), 'end': QColor(104, 46, 46),
            'dialogue': QColor(46, 68, 104), 'function': QColor(104, 104, 46),
            'jump': QColor(86, 46, 104), 'wait': QColor(70, 70, 70),
            'show': QColor(104, 76, 32), 'condition': QColor(128, 64, 128),
            'if_show_variant': QColor(128, 64, 128)
        }

    def set_data(self, nodes, connections):
        metrics = QFontMetrics(QFont("Consolas", 10))
        for node in nodes: node.calculate_height(metrics)
        self.nodes, self.connections = nodes, connections
        self._arrange_horizontal()
        self.update()

    def _arrange_horizontal(self):
        x, y = 100.0, 300.0
        spacing = 120.0
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
        for from_id, to_id in self.connections: self._draw_link(painter, from_id, to_id)
        for node in self.nodes: self._draw_node(painter, node)

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
            path = QPainterPath()
            path.moveTo(p1)
            if abs(p1.y() - p2.y()) > abs(p1.x() - p2.x()):
                cp1 = QPointF(p1.x(), p1.y() + (p2.y() - p1.y())/2)
                cp2 = QPointF(p2.x(), p2.y() - (p2.y() - p1.y())/2)
            else:
                dist = max(abs(p2.x() - p1.x()) * 0.5, 50.0)
                cp1 = QPointF(p1.x() + dist, p1.y())
                cp2 = QPointF(p2.x() - dist, p2.y())
            path.cubicTo(cp1, cp2, p2)
            painter.setPen(QPen(self.color_link, 2.2))
            painter.drawPath(path)

    def _draw_node(self, painter, node):
        renderer = self.renderer_factory.get_renderer(node.type, node.content)
        renderer.draw_node(painter, node, self)