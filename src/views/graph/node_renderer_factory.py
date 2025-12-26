from abc import ABC, abstractmethod
from PyQt5.QtGui import QPainter
from .standard_node_renderer import StandardNodeRenderer
from .conditional_node_renderer import ConditionalNodeRenderer
from .if_show_variant_node_renderer import IfShowVariantNodeRenderer

class NodeRenderer(ABC):
    @abstractmethod
    def draw_node(self, painter: QPainter, node, canvas):
        pass

class NodeRendererFactory:
    def __init__(self):
        self.renderers = {
            'standard': StandardNodeRenderer(),
            'condition': ConditionalNodeRenderer(),
            'if_show_variant': IfShowVariantNodeRenderer(),
        }

    def get_renderer(self, node_type: str, node_content: str = "") -> 'NodeRenderer':
        low_content = node_content.lower()
        low_type = node_type.lower()
        
        if 'if show variant' in low_content or 'variants:' in low_content or 'variant' in low_type:
            return self.renderers['if_show_variant']
        
        if low_type in ['condition', 'conditional', 'if']:
            return self.renderers['condition']

        return self.renderers['standard']

    def register_renderer(self, node_type: str, renderer: 'NodeRenderer'):
        self.renderers[node_type] = renderer