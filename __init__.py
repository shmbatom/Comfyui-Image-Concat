
# __init__.py
from .node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
# 告诉 ComfyUI 前端资源位置
WEB_DIRECTORY = "./js"
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']