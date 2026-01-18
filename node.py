import os
import math
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Global node registration dictionary
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


class ImageConcatNode:
    """✅A powerful image concatenation tool for ComfyUI, with True Alpha Channel Support and Multiple Image-title Fill Modes."""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                # 基础配置组
                "a1_image_dir": ("STRING", {"default": "", "placeholder": "Path to image folder"}),
                "a2_page_width": ("INT", {"default": 4000, "min": 100, "max": 50000, "step": 10}),
                "a3_page_aspect_ratio": ("COMBO", {
                    "default": "3:2",
                    "forceInput": False,
                    "options": ["10:1", "8:1", "5:1", "5:2", "16:9", "16:10", "3:2", "4:3", "1:1",
                                "3:4", "2:3", "10:16", "9:16", "2:5", "1:5", "1:8", "1:10"]
                }),
                "a4_cols_rows_per_page": ("INT", {
                    "default": 3,
                    "min": 1,
                    "max": 20,
                    "step": 1,
                    "label": "a4_行列数(每页) | Cols/Rows per Page",
                    "description": "- Mode1-5: 每行固定列数（整页所有行均为此列数）\n- Mode6: 每页固定行数"
                }),
                "a5_page_margin": ("INT", {"default": 50, "min": 0, "max": 500, "step": 1}),
                "a6_title_padding": ("INT", {"default": 30, "min": 0, "max": 200, "step": 1}),
                "a7_title_draw_mode": ("COMBO", {
                    "default": "3.zoom by long side (recommended)",
                    "forceInput": False,
                    "options": [
                        "1.smaller value filler",
                        "2.Stretches image to fill",
                        "3.zoom by long side (recommended)",
                        "4.crop square by short side",
                        "5.equal title width up_down",
                        "6.equal title height left_right"
                    ]
                }),
                "a8_title_first_position": ("COMBO", {
                    "default": "start_from margin",
                    "forceInput": False,
                    "options": [
                        "start_from margin",
                        "start_from margin + padding",
                        "start_from margin + padding(vertical centering)"
                    ]
                }),
                # 样式配置组
                "a9_background_style": ("COMBO", {
                    "default": "Light (white)",
                    "forceInput": False,
                    "options": ["Light (white)", "Dark (black)", "Transparent (alpha channel)"]
                }),
                "a10_title_border": ("COMBO", {
                    "default": "Rounded (radius=10px)",
                    "forceInput": False,
                    "options": ["None", "Rectangle", "Rounded (radius=10px)", "Rounded (radius=20px)"]
                }),
                "a11_title_border_style": ("COMBO", {
                    "default": "Solid",
                    "forceInput": False,
                    "options": ["Solid", "Dashed (4px,4px)", "Dashed (8px,8px)", "Dotted (1px,2px)",
                                "Dash-dot (8px,4ox,2px,4px)"]
                }),
                "a12_page_border": ("COMBO", {
                    "default": "Rounded (radius=30px)",
                    "forceInput": False,
                    "options": ["None", "Rectangle", "Rounded (radius=10px)", "Rounded (radius=20px)",
                                "Rounded (radius=30px)"]
                }),
                "a13_page_border_style": ("COMBO", {
                    "default": "Solid",
                    "forceInput": False,
                    "options": ["Solid", "Dashed (4px,4px)", "Dashed (8px,8px)", "Dotted (1px,2px)",
                                "Dash-dot (8px,4ox,2px,4px)"]
                }),
                "a14_filename_position": ("COMBO", {
                    "default": "none",
                    "forceInput": False,
                    "options": ["none", "above", "top", "middle", "bottom", "below"],
                    "label": "a16_文件名位置"
                }),
                "a15_filename_color": ("COMBO", {
                    "default": "black",
                    "forceInput": False,
                    "options": [
                        "black",
                        "white",
                        "red",
                        "dark red",
                        "blue",
                        "dark blue",
                        "green",
                        "dark green",
                        "yellow",
                        "orange",
                        "purple",
                        "pink",
                        "light gray",
                        "dark gray",
                        "slate gray",
                        "cyan",
                        "magenta"
                    ],
                    "label": "a17_文件名颜色"
                }),
                # 样式配置组
                "a97_title_save_mode": ("COMBO", {
                    "default": "none",
                    "forceInput": False,
                    "options": ["none", "save single title", "save single image"],
                    "label": "a97_title_save_mode"
                }),
                "a98_title_save_dir": (
                    "STRING", {"default": "./output/concat_titles", "placeholder": "title save directory path"}),
                "a99_title_save_filename": ("COMBO", {
                    "default": "source file name",
                    "forceInput": False,
                    "options": ["source file number", "source file name", "page + number"],
                    "label": "a99_title_save_filename"
                }),

            },
            "optional": {},
        }

    RETURN_TYPES = ("IMAGE", "INT", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = (
        "b1_concat_images", "b2_page_count", "b3_size_per_title", "b4_valid_image_count", "b5_title_save_path",
        "b6_help_info")
    FUNCTION = "generate_concat"
    CATEGORY = "Image Processing/concat"
    DESCRIPTION = "✅修复PageIdx未定义错误 | 文件名X轴居中修正 | 所有模式正常显示 | 自定义文件名颜色 | 独立图片保存模式"

    def get_node_tips(self):
        tips = """
    ===========================================================================
    📌    【 Parameter Guide - Image Concat V1.1 Official Manual 】 
                 【 参数说明 - Image Concat V1.1 官方手册 】   
                      【Email/邮箱 2540968810@qq.com】
    ===========================================================================

    【 I. Input Params A1~A17 Detailed Usage | 输入参数 A1 ~ A17 详细用法 】
    ---------------------------------------------------------------------------
    ▷ a1_image_dir     | 图片文件夹绝对路径，必填 | Absolute path of image folder (Required)
    ▷ a2_page_width    | 拼接画布总宽度(px)，高度由宽高比自动计算 | Total width of canvas(px), height auto-calculated by aspect ratio
    ▷ a3_page_aspect_ratio  | 画布整体宽高比 | Overall aspect ratio of canvas
                       | Options: 10:1 8:1 5:1 5:2 16:9 16:10 3:2 4:3 1:1 3:4 2:3 10:16 9:16 2:5 1:5 1:8 1:10
    ▷ a4_cols_rows_per_page | 全局通用队列数 | Global common queue count
                       | - Mode 1-4: 每行图片个数 (Columns per row)
                       | - Mode 5: 每列的块组数 (Groups per column)
                       | - Mode 6: 每页行数 (Rows per page)
    ▷ a5_page_margin     | 画布四边留白边距(px)  | Margin of canvas border(px) | Default=50
    ▷ a6_title_padding   | 图片块之间的间距(px)  | padding between image titles(px) | Default=30
    ▷ a7_title_draw_mode | 图片填充模式         | Image fill mode [Most Important]
                       | 1. smaller value filler: 等比缩放适配，留白填充 | Scale to fit, fill blank space
                       | 2. Stretches image to fill: 拉伸填满块 | Stretch to fill title (ignore ratio)
                       | 3. zoom by long side(recommend): 优先适配长边，等比缩放【推荐】| Fit long side first (Recommended)
                       | 4. crop square by short side: 裁剪短边为正方形后缩放  | Crop short side to square then scale
                       | 5. equal title width up_down: 等宽模式，纵向直连     | Equal-width mode, vertical connection
                       | 6. equal title height left_right: 等高模式，横向直连 | Equal-height mode, horizontal connection
    ▷ a8_title_first_position | 图片块起始绘制位置 | Image title start position
                       | ① start_from margin: 从边距处开始绘制 | Start at margin (Default)
                       | ② start_from margin + padding: 边距+间距处开始 | Start at margin+padding
                       | ③ start_from margin + padding(vertical centering): 垂直居中绘制 | Vertical centering
    ▷ a9_background_style | 画布背景样式 | Canvas background style
                       | Options: Light (white)/Dark (black)/Transparent (alpha channel)
    ▷ a10_title_border | 单个图片块的边框样式 | Single image title border style
                       | Options: None/Rectangle/Rounded (radius=10px)/Rounded (radius=20px)
    ▷ a11_title_border_style | 块边框线型 | title border line style
                       | Options: Solid/Dashed (4px,4px)/Dashed (8px,8px)/Dotted (1px,2px)/Dash-dot (8px,4ox,2px,4px)
    ▷ a12_page_border  | 整页画布的外边框样式 | Whole page border style
                       | Options: None/Rectangle/Rounded (radius 10/20/30)
    ▷ a13_page_border_style | 画布外边框线型 | Page border line style | Same as title border options
    ▷ a14_filename_position | 文件名显示位置 | Filename display position
                       | none: 不显示 | above: 图块上方 | top: 图片内顶部
                       | middle: 图片内中部 | bottom: 图片内底部 | below: 图块下方
    ▷ a15_filename_color | 文件名显示颜色 | Filename display color
                       | Options: black/white/red/dark red/blue/dark blue/green/dark green
                       | /yellow/orange/purple/pink/light gray/dark gray/slate gray/cyan/magenta
    ▷ a97_title_save_mode | 独立块保存模式 | Save individual title mode
                       | none: 不保存 | save single title: 保存为title(含留白) | save single image: 保存为原始图(无留白)
    ▷ a98_title_save_dir | 独立块保存路径 | Save path of individual titles | Default=./output/concat_titles
    ▷ a99_title_save_filename | 独立块文件命名模式 | Save filename mode
                       | source file number: 按序号命名 (00001.jpg...)                     
                       | source file name: 使用原文件名 (默认) 
                       | page + number: 页码+序号 (p1_1.png...)，序号从1开始

    【 II. Output Params B1~B6 Detailed Meaning | 输出参数 B1 ~ B6 详细含义 】
    ---------------------------------------------------------------------------
    ▷ b1_concat_images | 拼接完成的最终图片张量 | Final concatenated image tensor
                       | Can connect to Save Image node directly, multi-page as batch tensor
    ▷ b2_page_count    | 本次拼接生成的总页数(整数) | Total pages of concatenation (Integer) | For counting/renaming
    ▷ b3_size_per_title  | 单图片块的基准尺寸(字符串) | Base size of single image title (String) | e.g. 300×300
    ▷ b4_valid_image_count | 读取到的有效图片总数 | Total valid images read (Integer) | For verification
    ▷ b5_title_save_path | 独立块的最终保存路径 | Final save path of individual titles (String) | With timestamp
    ▷ b6_help_info     | 本帮助手册 | This help manual | Real-time parameter reference

    【 III. Core Features & Optimization Log | 核心特性与更新日志 】 
    ---------------------------------------------------------------------------
      ✅ 1. Flexible Fill Modes (A7): | 灵活填充模式 (A7):
         • Mode 1-4 (Grid): "Smaller value", "Stretch", "Zoom Long side (Best)", "Crop Square".
             Provides full control over how images fit into their grid titles.
             (1-4网格模式：提供多种方式控制图片适配网格块)
         • Mode 5 (Equal Width): Keeps columns same width. Images stack vertically. Good for long strips.
             (5等宽模式：保持列宽一致，图片纵向堆叠，适合长图拼接)
         • Mode 6 (Equal Height): Keeps rows same height. Images stack horizontally. Good for panoramas.
             (6等高模式：保持行高一致，图片横向堆叠，适合全景图)

      ✅ 2. Smart Alignment (A8): | 智能对齐 (A8):
         • "Vertical Centering": Automatically centers content vertically on the canvas when pages are not full.
             (垂直居中：当页面未填满时，自动在画布垂直方向居中内容)
         • "Last Row Centering": In multi-column modes (A4>1), if the last row is incomplete, it is centered.
             (末行居中：多列模式下，若最后一行未满，自动居中显示)

      ✅ 3. Customizable Text & Style (A14, A15): | 自定义文本与样式 (A14, A15):
         • Position: Show filenames (out of title: above/below, inside of title: top/middle/bottom). 
             (位置：显示文件名，位于图块或图片不同位置。)
         • Color: Choose from 16 distinct colors (Black, White, Red, Blue, etc.) to suit any background.
             (颜色：提供16种颜色选择，适配各种背景风格)

      ✅ 4. Rich Borders & Backgrounds (A9-A12, A10-A11): | 丰富边框与背景 (A9-A12, A10-A11):
         • Solid or Dashed borders with custom radius. 
         • Light, Dark, or Transparent backgrounds.
             (实线/虚线边框及圆角设置。支持白色/黑色/透明背景)

      ✅ 5. New Save Mode (A98, A99): | 新增保存模式 (A98, A99):
         • "Save single image": Saves the image without whitespace/padding (e.g., 1024x768).
             (新增：保存原始图，去除title边距留白，例如1024x768)
         • "Save single title": Saves the image within the title canvas (e.g., 1024x1024).
             (保存title模式，包含边距留白，例如1024x1024)

        """
        return tips

    def convert_ratio_to_float(self, ratio_str):
        try:
            width_part, height_part = ratio_str.split(":")
            width_num = float(width_part)
            height_num = float(height_part)
            return width_num / height_num
        except (ValueError, IndexError) as e:
            print(f"[Warning] Invalid ratio format: {ratio_str}, using default 1.5 (3:2)")
            return 1.5

    def get_filename_color_by_name(self, color_name):
        """根据用户选择的颜色名称返回 RGB 值"""
        color_map = {
            "black": (0, 0, 0),
            "white": (255, 255, 255),
            "red": (255, 0, 0),
            "dark red": (139, 0, 0),
            "blue": (0, 0, 255),
            "dark blue": (0, 0, 139),
            "green": (0, 255, 0),
            "dark green": (0, 100, 0),
            "yellow": (255, 255, 0),
            "orange": (255, 165, 0),
            "purple": (128, 0, 128),
            "pink": (255, 192, 203),
            "light gray": (220, 220, 220),
            "dark gray": (40, 40, 40),
            "slate gray": (112, 128, 144),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255)
        }
        return color_map.get(color_name, (0, 0, 0))  # 默认返回黑色

    def get_dash_pattern(self, style_name):
        if style_name == "Solid":
            dash_pattern = None
        elif style_name == "Dashed (4px,4px)":
            dash_pattern = (4, 4)
        elif style_name == "Dashed (8px,8px)":
            dash_pattern = (8, 8)
        elif style_name == "Dotted (1px,2px)":
            dash_pattern = (1, 2)
        elif style_name == "Dash-dot (8px,4ox,2px,4px)":
            dash_pattern = (8, 4, 2, 4)
        else:
            dash_pattern = None
        return dash_pattern

    def draw_dashed_line_manual(self, draw, start, end, dash_pattern, width=2, color='black'):
        if dash_pattern is None or len(dash_pattern) < 2:
            draw.line([start, end], fill=color, width=width)
            return

        x1, y1 = start
        x2, y2 = end
        dx = x2 - x1
        dy = y2 - y1
        length = math.hypot(dx, dy)
        if length == 0:
            return

        ux = dx / length
        uy = dy / length
        dash_on, dash_off = dash_pattern[:2] if len(dash_pattern) >= 2 else (1, 1)
        current_pos = 0
        draw_on = True

        while current_pos < length:
            if draw_on:
                segment_length = min(dash_on, length - current_pos)
                seg_end_x = x1 + ux * (current_pos + segment_length)
                seg_end_y = y1 + uy * (current_pos + segment_length)
                draw.line([(x1 + ux * current_pos, y1 + uy * current_pos), (seg_end_x, seg_end_y)], fill=color,
                          width=width)
                current_pos += segment_length
            else:
                current_pos += dash_off
                draw_on = not draw_on

    def draw_dashed_rectangle_manual(self, draw, rect, dash_pattern, width=2, color='black'):
        x1, y1, x2, y2 = rect
        self.draw_dashed_line_manual(draw, (x1, y1), (x2, y1), dash_pattern, width, color)
        self.draw_dashed_line_manual(draw, (x2, y1), (x2, y2), dash_pattern, width, color)
        self.draw_dashed_line_manual(draw, (x2, y2), (x1, y2), dash_pattern, width, color)
        self.draw_dashed_line_manual(draw, (x1, y2), (x1, y1), dash_pattern, width, color)

    def draw_dashed_rounded_rectangle_manual(self, draw, rect, radius, dash_pattern, width=2, color='black'):
        x1, y1, x2, y2 = rect
        r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
        draw.arc([x1, y1, x1 + 2 * r, y1 + 2 * r], 180, 270, fill=color, width=width)
        draw.arc([x2 - 2 * r, y1, x2, y1 + 2 * r], 270, 0, fill=color, width=width)
        draw.arc([x2 - 2 * r, y2 - 2 * r, x2, y2], 0, 90, fill=color, width=width)
        draw.arc([x1, y2 - 2 * r, x1 + 2 * r, y2], 90, 180, fill=color, width=width)
        self.draw_dashed_line_manual(draw, (x1 + r, y1), (x2 - r, y1), dash_pattern, width, color)
        self.draw_dashed_line_manual(draw, (x2, y1 + r), (x2, y2 - r), dash_pattern, width, color)
        self.draw_dashed_line_manual(draw, (x2 - r, y2), (x1 + r, y2), dash_pattern, width, color)
        self.draw_dashed_line_manual(draw, (x1, y2 - r), (x1, y1 + r), dash_pattern, width, color)

    def crop_center_square(self, img):
        width, height = img.size
        square_size = min(width, height)
        left = (width - square_size) / 2
        top = (height - square_size) / 2
        right = (width + square_size) / 2
        bottom = (height + square_size) / 2
        return img.crop((left, top, right, bottom))

    def get_background_config(self, background_style):
        if background_style == "Light (white)":
            return (255, 255, 255), 'RGB'
        elif background_style == "Dark (black)":
            return (0, 0, 0), 'RGB'
        elif background_style == "Transparent (alpha channel)":
            return (0, 0, 0, 0), 'RGBA'
        else:
            return (255, 255, 255), 'RGB'

    def get_border_color(self, background_style):
        if background_style == "Dark (black)":
            return 'white'
        else:
            return 'black'

    def get_font(self, font_size):
        try:
            if os.name == 'nt':
                font = ImageFont.truetype("simhei.ttf", font_size)
            else:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            font = ImageFont.load_default(size=font_size)
        return font

    def save_single_title(self, img_resized, title_border, title_border_style,
                          save_dir, filename, add_filename, filename_color, save_mode, save_filename_mode,
                          page_num, idx, global_idx, w_title, h_title, border_width=2,
                          background_style="Light (white)"):
        bg_color, img_mode = self.get_background_config(background_style)
        border_color = self.get_border_color(background_style)

        # ========== 优化：去除文件名后缀 ==========
        draw_name = os.path.splitext(filename)[0]
        # =========================================

        # ========== 统一文件名映射逻辑 ==========
        # 无论是在 title 还是 Image 模式下，统一处理 above/below 的映射
        effective_add_filename = add_filename
        if effective_add_filename == "above":
            effective_add_filename = "top"
        elif effective_add_filename == "below":
            effective_add_filename = "bottom"
        # =========================================

        # ========== 生成保存路径 ==========
        if save_filename_mode == "source file number":
            # 格式: 00001.ext
            _, ext = os.path.splitext(filename)
            # 保留原始扩展名，如果原始扩展名非图片后缀，默认使用png
            # 此处简单保留原扩展名
            save_name = f"{global_idx + 1:05d}{ext}"
        elif save_filename_mode == "page + number":
            # 格式: p1_1.png (idx from 1)
            save_name = f"p{page_num}_{idx + 1}.png"
        else:  # source file name
            save_name = filename

        save_path = os.path.join(save_dir, save_name)
        # ======================================

        # ========== save single image 模式逻辑 ==========
        if save_mode == "image":
            # 使用图片实际尺寸作为画布大小
            canvas_w = img_resized.width
            canvas_h = img_resized.height
            title_canvas = Image.new(img_mode, (canvas_w, canvas_h), color=bg_color)

            # 粘贴图片（左上角对齐）
            title_canvas.paste(img_resized, (0, 0))

            # 文件名绘制
            if effective_add_filename != "none" and filename:
                draw = ImageDraw.Draw(title_canvas)
                # 动态计算字体大小
                font_size = int(min(canvas_w, canvas_h) * 0.05)
                font = self.get_font(max(font_size, 10))
                text_bbox = draw.textbbox((0, 0), draw_name, font=font)
                text_w = text_bbox[2] - text_bbox[0]
                text_h = text_bbox[3] - text_bbox[1]

                text_x = (canvas_w - text_w) // 2
                gap = 8

                # 以图形边缘为界绘制
                if effective_add_filename == "top":
                    text_y = gap
                elif effective_add_filename == "middle":
                    text_y = (canvas_h - text_h) // 2
                elif effective_add_filename == "bottom":
                    text_y = canvas_h - text_h - gap
                else:
                    text_y = 0

                draw.text((text_x, text_y), draw_name, fill=filename_color, font=font)

            # 边框绘制
            if title_border != "None":
                draw = ImageDraw.Draw(title_canvas)
                dash_pattern = self.get_dash_pattern(title_border_style)
                border_rect = [0, 0, canvas_w, canvas_h]

                if "Rounded" in title_border:
                    radius = 10 if "10" in title_border else 20
                    self.draw_dashed_rounded_rectangle_manual(
                        draw, border_rect, radius, dash_pattern,
                        border_width, color=border_color
                    )
                else:
                    self.draw_dashed_rectangle_manual(
                        draw, border_rect, dash_pattern,
                        border_width, color=border_color
                    )
            title_canvas.save(save_path, 'PNG', quality=100, pnginfo=None, optimize=False)
            return
        # =================================================

        # ========== save single title 模式逻辑 (已优化) ==========
        title_canvas = Image.new(img_mode, (int(w_title), int(h_title)), color=bg_color)
        img_x = (int(w_title) - img_resized.width) // 2
        img_y = (int(h_title) - img_resized.height) // 2

        if img_resized.mode == 'RGB' and img_mode == 'RGBA':
            img_resized = img_resized.convert('RGBA')
            img_resized.putalpha(Image.new('L', img_resized.size, 255))

        mask = img_resized.split()[-1] if img_mode == 'RGBA' else None
        title_canvas.paste(img_resized, (img_x, img_y), mask=mask)

        if effective_add_filename != "none" and filename:
            draw = ImageDraw.Draw(title_canvas)
            font_size = int(min(w_title, h_title) * 0.05)
            font = self.get_font(font_size)
            text_bbox = draw.textbbox((0, 0), draw_name, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            text_h = text_bbox[3] - text_bbox[1]

            text_x = (int(w_title) - text_w) // 2
            gap = 8

            # 以 title 边缘为界绘制
            if effective_add_filename == "top":
                text_y = gap
            elif effective_add_filename == "middle":
                text_y = (int(h_title) - text_h) // 2
            elif effective_add_filename == "bottom":
                text_y = int(h_title) - text_h - gap
            else:
                text_y = 0

            draw.text((text_x, text_y), draw_name, fill=filename_color, font=font)

        if title_border != "None":
            draw = ImageDraw.Draw(title_canvas)
            dash_pattern = self.get_dash_pattern(title_border_style)
            border_rect = [0, 0, int(w_title), int(h_title)]

            if "Rounded" in title_border:
                radius = 10 if "10" in title_border else 20
                self.draw_dashed_rounded_rectangle_manual(
                    draw, border_rect, radius, dash_pattern,
                    border_width, color=border_color
                )
            else:
                self.draw_dashed_rectangle_manual(
                    draw, border_rect, dash_pattern,
                    border_width, color=border_color
                )
        title_canvas.save(save_path, 'PNG', quality=100, pnginfo=None, optimize=False)

    def calc_vertical_title_groups_a4_1(self, image_files, width_page_use, height_page_use, padding, a7_mode, a8_mode):
        if not image_files:
            return []

        try:
            with Image.open(os.path.join(self.image_dir_full, image_files[0])) as img:
                first_w, first_h = img.size
        except:
            first_w, first_h = 100, 100

        if first_w <= 0 or first_h <= 0:
            first_w, first_h = 100, 100

        global_meta = {'type': '', 'size': 0, 'width': 0, 'height': 0, 'layout': 'vertical'}
        has_outer_padding = (a7_mode != "start_from margin")

        if a8_mode in ["1.smaller value filler", "2.Stretches image to fill",
                       "3.zoom by long side (recommended)", "4.crop square by short side"]:
            limit_w = width_page_use - (2 * padding if has_outer_padding else 0)
            limit_w = max(limit_w, 10)
            title_size = min(first_w, limit_w)
            global_meta = {'type': 'square', 'size': int(title_size), 'layout': 'vertical'}

        elif a8_mode == "5.equal title width up_down":
            base_w = min(width_page_use, first_w)
            h_limit = height_page_use - (2 * padding if has_outer_padding else 0)
            while base_w > 0:
                calc_h = int(base_w * (first_h / first_w)) if first_w > 0 else 100
                if calc_h <= h_limit:
                    break
                base_w -= 10
            global_meta = {'type': 'fixed_width', 'width': int(base_w), 'layout': 'vertical'}

        elif a8_mode == "6.equal title height left_right":
            base_h = min(height_page_use, first_h)
            w_limit = width_page_use - (2 * padding if has_outer_padding else 0)
            while base_h > 0:
                calc_w = int(base_h * (first_w / first_h)) if first_h > 0 else 100
                if calc_w <= w_limit:
                    break
                base_h -= 10
            global_meta = {'type': 'fixed_height', 'height': int(base_h), 'layout': 'horizontal'}

        pages = []
        idx = 0

        while idx < len(image_files):
            current_page_images = []

            is_horizontal = (global_meta['layout'] == 'horizontal')

            if is_horizontal:
                cursor = 0
                if a7_mode != "start_from margin":
                    cursor += padding
                limit = width_page_use
            else:
                cursor = 0
                if a7_mode != "start_from margin":
                    cursor += padding
                limit = height_page_use

            while idx < len(image_files):
                img_file = image_files[idx]
                try:
                    with Image.open(os.path.join(self.image_dir_full, img_file)) as img:
                        cur_w, cur_h = img.size
                except:
                    cur_w, cur_h = 100, 100

                if cur_w <= 0 or cur_h <= 0:
                    cur_w, cur_h = 100, 100

                dim = 0
                if global_meta['type'] == 'square':
                    dim = global_meta['size']
                elif global_meta['type'] == 'fixed_width':
                    bw = global_meta['width']
                    ratio = cur_h / cur_w if cur_w > 0 else 1
                    dim = int(bw * ratio)
                elif global_meta['type'] == 'fixed_height':
                    bh = global_meta['height']
                    ratio = cur_w / cur_h if cur_h > 0 else 1
                    dim = int(bh * ratio)

                dim = max(dim, 1)

                if len(current_page_images) == 0:
                    if dim > limit:
                        dim = limit
                else:
                    if cursor + padding + dim > limit:
                        break

                current_page_images.append(img_file)

                if len(current_page_images) == 0:
                    cursor += dim
                else:
                    cursor += padding + dim

                idx += 1

            pages.append({'files': current_page_images, 'meta': global_meta})

        return pages

    def calc_unified_base_width_n1(self, img_org_w, img_org_h, width_page_use, height_page_use, title_first_position,
                                   padding, theory_w_title):
        if title_first_position == "start_from margin":
            limit_width = width_page_use
            limit_height = height_page_use
        else:
            limit_width = width_page_use - 2 * padding
            limit_height = height_page_use - 2 * padding

        img_ratio = img_org_w / img_org_h
        init_base_w = min(theory_w_title, limit_width, img_org_w)
        init_base_h = int(init_base_w / img_ratio)

        unified_base_w = init_base_w
        if init_base_h > limit_height:
            unified_base_w = int(limit_height * img_ratio)
            unified_base_w = min(unified_base_w, limit_width)
            print(
                f"[✅n=1反推生效] 首图高度超限 {init_base_h} > {limit_height} → 本页统一基准宽锁定: {unified_base_w}px")
        else:
            print(f"[✅n=1合规生效] 首图尺寸合规 → 本页统一基准宽锁定: {unified_base_w}px")

        return unified_base_w

    def calc_vertical_title_groups(self, image_files, height_page_use, padding, title_first_position, w_title_size_int,
                                   n_per_row):
        h_diff_title_size = []
        img_wh_list = []
        for img_file in image_files:
            try:
                img_path = os.path.join(self.image_dir_full, img_file)
                img = Image.open(img_path).convert('RGB')
                img_wh_list.append((img.width, img.height))
            except Exception as e:
                print(f"[Error] Read img {img_file} failed: {e}")
                img_wh_list.append((w_title_size_int, w_title_size_int))

        title_groups = []
        h_title_group_size = []
        current_group = []
        current_col_height = 0
        page_height_limit = height_page_use
        current_page_lock_w = w_title_size_int

        for idx, (img_w, img_h) in enumerate(img_wh_list):
            img_ratio = img_w / img_h
            new_img_h = 0

            if n_per_row == 1:
                if len(current_group) == 0:
                    current_page_lock_w = self.calc_unified_base_width_n1(
                        img_w, img_h, self.width_page_use_global, height_page_use,
                        title_first_position, padding, w_title_size_int
                    )
                new_img_h = int(current_page_lock_w / img_ratio)

            else:
                scale_ratio = w_title_size_int / img_w
                new_img_h = int(img_h * scale_ratio)

            h_diff_title_size.append(new_img_h)

            temp_bottom_y = new_img_h if len(current_group) == 0 else current_col_height + padding + new_img_h
            if temp_bottom_y > page_height_limit and len(current_group) > 0:
                title_groups.append(current_group)
                n = len(current_group)
                group_h = sum(h_diff_title_size[i] for i in current_group) + (n - 1) * padding
                h_title_group_size.append(group_h)
                current_group = [idx]
                current_col_height = new_img_h
            else:
                current_group.append(idx)
                current_col_height = temp_bottom_y

        if len(current_group) > 0:
            title_groups.append(current_group)
            n = len(current_group)
            group_h = sum(h_diff_title_size[i] for i in current_group) + (n - 1) * padding
            h_title_group_size.append(group_h)

        print(f"[✅等宽模式] 生成 {len(title_groups)} 个纵向块组 | 组高度(精准公式): {h_title_group_size}")
        return h_diff_title_size, h_title_group_size, title_groups, current_page_lock_w if n_per_row == 1 else w_title_size_int

    def calc_h_each_row(self, height_page_use, padding, title_first_position, n_per_queue):
        h_each_row_guess = 0
        if title_first_position == "start_from margin":
            h_each_row_guess = int((height_page_use - (n_per_queue - 1) * padding) / n_per_queue)
        else:
            h_each_row_guess = int((height_page_use - (n_per_queue + 1) * padding) / n_per_queue)
        h_each_row = max(h_each_row_guess, 20)
        print(f"[✅等高模式行高计算完成] a7={title_first_position} | 最终行高 h_each_row = {h_each_row} px")
        return h_each_row

    def calc_horizontal_row_groups(self, image_files, width_page_use, height_page_use, padding, title_first_position,
                                   h_title_size_int, n_per_row):
        w_diff_title_size = []
        img_wh_list = []
        for img_file in image_files:
            try:
                img_path = os.path.join(self.image_dir_full, img_file)
                img = Image.open(img_path).convert('RGB')
                img_wh_list.append((img.width, img.height))
            except Exception as e:
                print(f"[Error] Read img {img_file} failed: {e}")
                img_wh_list.append((h_title_size_int, h_title_size_int))

        h_each_row = self.calc_h_each_row(height_page_use, padding, title_first_position, n_per_row)

        for img_w, img_h in img_wh_list:
            img_ratio = img_w / img_h
            new_img_w = int(h_each_row * img_ratio)
            w_diff_title_size.append(new_img_w)

        row_groups = []
        w_row_group_size = []
        current_row = []
        current_row_width = 0

        for idx, img_w_calc in enumerate(w_diff_title_size):
            n = len(current_row)
            if n == 0:
                current_row.append(idx)
                current_row_width = img_w_calc
            else:
                if title_first_position == "start_from margin":
                    judge_width = current_row_width + img_w_calc + (n - 1) * padding
                else:
                    judge_width = current_row_width + img_w_calc + (n + 1) * padding

                if judge_width > width_page_use:
                    row_groups.append(current_row)
                    row_w = sum(w_diff_title_size[i] for i in current_row) + (len(current_row) - 1) * padding
                    w_row_group_size.append(row_w)
                    current_row = [idx]
                    current_row_width = img_w_calc
                else:
                    current_row.append(idx)
                    current_row_width += img_w_calc

        if len(current_row) > 0:
            row_groups.append(current_row)
            row_w = sum(w_diff_title_size[i] for i in current_row) + (len(current_row) - 1) * padding
            w_row_group_size.append(row_w)

        total_rows = len(row_groups)
        rows_per_page = n_per_row
        page_row_mapping = []
        page_total_occupy_h = []
        for i in range(0, total_rows, rows_per_page):
            page_rows = row_groups[i:i + rows_per_page]
            page_row_mapping.append(page_rows)
            if title_first_position == "start_from margin":
                page_h = len(page_rows) * h_each_row + (len(page_rows) - 1) * padding
            else:
                page_h = len(page_rows) * h_each_row + (len(page_rows) + 1) * padding
            page_total_occupy_h.append(page_h)

        print(
            f"[✅等高模式] 生成 {len(row_groups)} 个横向行组 | 分页后总页数: {len(page_row_mapping)} | 行宽度列表: {w_row_group_size}")
        return w_diff_title_size, w_row_group_size, row_groups, page_row_mapping, page_total_occupy_h, h_each_row

    def create_single_concat_page(self, image_files_page, width_page, height_page, n_per_row, n_per_col_int,
                                  margin, padding, title_first_position,
                                  w_title_size, h_title_size, draw_mode, title_border, title_border_style,
                                  page_border, page_border_style, page_num,
                                  save_mode, titles_save_dir, save_filename_mode, global_start_idx,
                                  background_style, vertical_offset_mode,
                                  image_count_in_dir, current_page_group_count=0, page_total_occupy_h=0,
                                  add_filename="none", page_meta=None, filename_color="black"):
        width_page_int = int(round(width_page))
        height_page_int = int(round(height_page))
        w_title_size_int = int(round(w_title_size))
        h_title_size_int = int(round(h_title_size))

        is_a4_equals_1 = (page_meta is not None)

        is_start_from_margin = (title_first_position == "start_from margin")
        is_vert_center = (title_first_position == "start_from margin + padding(vertical centering)")
        has_outer_padding = (not is_start_from_margin)

        w_title_size_int = int(round(w_title_size)) if w_title_size > 0 else 100
        h_title_size_int = int(round(h_title_size)) if h_title_size > 0 else 100

        if is_a4_equals_1:
            if page_meta['type'] == 'square':
                w_title_size_int = page_meta['size']
                h_title_size_int = page_meta['size']
            elif page_meta['type'] == 'fixed_width':
                w_title_size_int = page_meta['width']
                h_title_size_int = -1
            elif page_meta['type'] == 'fixed_height':
                w_title_size_int = -1
                h_title_size_int = page_meta['height']
        else:
            if draw_mode in ["1.smaller value filler", "2.Stretches image to fill",
                             "3.zoom by long side (recommended)", "4.crop square by short side"]:
                w_title_size_int = h_title_size_int = int(w_title_size)

        bg_color, img_mode = self.get_background_config(background_style)
        border_color = self.get_border_color(background_style)

        concat = Image.new(img_mode, (width_page_int, height_page_int), color=bg_color)
        draw = ImageDraw.Draw(concat)

        dash_title = self.get_dash_pattern(title_border_style)
        dash_page = self.get_dash_pattern(page_border_style)

        height_page_use = height_page - 2 * margin
        width_page_use = width_page - 2 * margin

        filename_draw_info = []

        if is_a4_equals_1:
            is_horizontal_layout = (page_meta.get('layout') == 'horizontal')

            if is_horizontal_layout:
                # Mode 6: Horizontal
                dims = []
                for img_file in image_files_page:
                    try:
                        with Image.open(os.path.join(self.image_dir_full, img_file)) as img:
                            orig_w, orig_h = img.size
                            if orig_w <= 0 or orig_h <= 0: orig_w, orig_h = 100, 100
                    except:
                        orig_w, orig_h = 100, 100
                    ratio = orig_w / orig_h if orig_h > 0 else 1
                    dw = int(h_title_size_int * ratio)
                    dims.append(dw)

                if has_outer_padding:
                    total_w = sum(dims) + (len(dims) + 1) * padding
                else:
                    total_w = sum(dims) + (len(dims) - 1) * padding
                x_offset = int((width_page_use - total_w) / 2)

                h_content = h_title_size_int
                if has_outer_padding:
                    h_content += 2 * padding
                y_offset = int((height_page_use - h_content) / 2)

                cursor_x = margin + x_offset
                cursor_y = margin + y_offset

                for idx, img_file in enumerate(image_files_page):
                    dw = dims[idx]
                    current_global_idx = global_start_idx + idx
                    try:
                        img = Image.open(os.path.join(self.image_dir_full, img_file)).convert('RGB')
                        orig_w, orig_h = img.size
                        if orig_w <= 0 or orig_h <= 0: orig_w, orig_h = 100, 100

                        dh = h_title_size_int
                        ratio = orig_w / orig_h if orig_h > 0 else 1
                        dw_calc = int(dh * ratio)

                        img_resized = img.resize((dw_calc, dh), Image.Resampling.LANCZOS)

                        title_x = cursor_x
                        title_y = cursor_y
                        if has_outer_padding:
                            title_x += padding

                        img_draw_x = title_x + (dw_calc - img_resized.width) // 2
                        img_draw_y = title_y

                        # Save Logic
                        if save_mode != "none":
                            self.save_single_title(img_resized, title_border, title_border_style,
                                                   titles_save_dir, img_file, add_filename, filename_color,
                                                   "title" if save_mode == "save single title" else "image",
                                                   save_filename_mode, page_num, idx, current_global_idx,
                                                   dw_calc, dh, background_style=background_style)

                        if img_resized.mode == 'RGB' and img_mode == 'RGBA':
                            img_resized = img_resized.convert('RGBA')
                            img_resized.putalpha(Image.new('L', img_resized.size, 255))
                        mask = img_resized.split()[-1] if img_mode == 'RGBA' else None
                        concat.paste(img_resized, (int(img_draw_x), int(img_draw_y)), mask=mask)

                        if title_border != "None":
                            rect = [int(title_x), int(title_y), int(title_x + dw_calc), int(title_y + dh)]
                            if "Rounded" in title_border:
                                self.draw_dashed_rounded_rectangle_manual(draw, rect, 10, dash_title, 2, border_color)
                            else:
                                self.draw_dashed_rectangle_manual(draw, rect, dash_title, 2, border_color)

                        # Filename Queue
                        if add_filename != "none":
                            # 修正：直接使用传入的颜色
                            text_color = filename_color

                            font_size = int(min(dw_calc, dh) * 0.05)
                            font = self.get_font(max(font_size, 10))
                            text_bbox = draw.textbbox((0, 0), img_file, font=font)
                            text_w = text_bbox[2] - text_bbox[0]
                            text_h = text_bbox[3] - text_bbox[1]
                            text_x = title_x + (dw_calc - text_w) // 2
                            gap = 8
                            if add_filename == "above":
                                text_y = title_y - text_h - gap
                            elif add_filename == "top":
                                text_y = img_draw_y + gap
                            elif add_filename == "middle":
                                text_y = img_draw_y + (dh - text_h) // 2
                            elif add_filename == "bottom":
                                text_y = img_draw_y + dh - text_h - gap
                            elif add_filename == "below":
                                text_y = title_y + dh + gap
                            # bg设为None，移除衬底
                            filename_draw_info.append({'xy': (text_x, text_y),
                                                       'rect': [text_x - 5, text_y - 2, text_x + text_w + 5,
                                                                text_y + text_h + 2], 'text': img_file, 'font': font,
                                                       'fill': text_color, 'bg': None})

                        cursor_x += dw_calc + padding
                    except Exception as e:
                        print(f"[Error] a4=1 mode6 draw {idx}: {e}")
            else:
                # Mode 1-5: Vertical
                dims = []
                for img_file in image_files_page:
                    try:
                        with Image.open(os.path.join(self.image_dir_full, img_file)) as img:
                            orig_w, orig_h = img.size
                            if orig_w <= 0 or orig_h <= 0: orig_w, orig_h = 100, 100
                    except:
                        orig_w, orig_h = 100, 100

                    if page_meta['type'] == 'square':
                        dh = w_title_size_int
                    elif page_meta['type'] == 'fixed_width':
                        dh = int(w_title_size_int * (orig_h / orig_w if orig_w > 0 else 1))
                    dims.append(max(dh, 1))

                n = len(dims)
                if is_vert_center:
                    if has_outer_padding:
                        total_h = (n + 1) * padding + sum(dims)
                    else:
                        total_h = (n - 1) * padding + sum(dims)
                    offset = int((height_page_use - total_h) / 2)
                    cursor_y = margin + offset
                else:
                    if has_outer_padding:
                        cursor_y = margin + padding
                    else:
                        cursor_y = margin

                content_w = w_title_size_int
                x_offset = int((width_page_use - content_w) / 2)
                cursor_x_base = margin + x_offset

                for idx, img_file in enumerate(image_files_page):
                    dh = dims[idx]
                    dw = w_title_size_int
                    current_global_idx = global_start_idx + idx

                    title_x = cursor_x_base
                    title_y = cursor_y

                    if idx == 0 and has_outer_padding:
                        title_y += padding
                    elif idx > 0:
                        title_y += padding

                    try:
                        img = Image.open(os.path.join(self.image_dir_full, img_file)).convert('RGB')
                        orig_w, orig_h = img.size
                        if orig_w <= 0 or orig_h <= 0: orig_w, orig_h = 100, 100

                        if page_meta['type'] == 'square':
                            if draw_mode == "2.Stretches image to fill":
                                img_resized = img.resize((dw, dh), Image.Resampling.LANCZOS)
                            elif draw_mode == "1.smaller value filler":
                                long_side = max(orig_w, orig_h)
                                target_side = min(long_side, dw)
                                scale = target_side / long_side
                                new_w = int(orig_w * scale);
                                new_h = int(orig_h * scale)
                                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                            elif draw_mode == "3.zoom by long side (recommended)":
                                long_side = max(orig_w, orig_h)
                                scale = dw / long_side
                                new_w = int(orig_w * scale);
                                new_h = int(orig_h * scale)
                                img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                            elif draw_mode == "4.crop square by short side":
                                img_sq = self.crop_center_square(img)
                                img_resized = img_sq.resize((dw, dh), Image.Resampling.LANCZOS)
                        else:
                            img_resized = img.resize((dw, dh), Image.Resampling.LANCZOS)

                        img_draw_x = title_x
                        img_draw_y = title_y
                        if page_meta['type'] == 'square':
                            img_draw_x += (dw - img_resized.width) // 2
                            img_draw_y += (dh - img_resized.height) // 2
                        elif page_meta['type'] == 'fixed_width':
                            img_draw_y += (dh - img_resized.height) // 2

                        # Save Logic
                        if save_mode != "none":
                            self.save_single_title(img_resized, title_border, title_border_style,
                                                   titles_save_dir, img_file, add_filename, filename_color,
                                                   "title" if save_mode == "save single title" else "image",
                                                   save_filename_mode, page_num, idx, current_global_idx,
                                                   dw, dh, background_style=background_style)

                        if img_resized.mode == 'RGB' and img_mode == 'RGBA':
                            img_resized = img_resized.convert('RGBA')
                            img_resized.putalpha(Image.new('L', img_resized.size, 255))
                        mask = img_resized.split()[-1] if img_mode == 'RGBA' else None
                        concat.paste(img_resized, (int(img_draw_x), int(img_draw_y)), mask=mask)

                        if title_border != "None":
                            if page_meta['type'] == 'square':
                                rect = [int(title_x), int(title_y), int(title_x + dw), int(title_y + dh)]
                            else:
                                rect = [int(title_x), int(title_y), int(title_x + img_resized.width),
                                        int(title_y + img_resized.height)]
                            if "Rounded" in title_border:
                                self.draw_dashed_rounded_rectangle_manual(draw, rect, 10, dash_title, 2, border_color)
                            else:
                                self.draw_dashed_rectangle_manual(draw, rect, dash_title, 2, border_color)

                        # Filename Queue
                        if add_filename != "none":
                            text_color = filename_color

                            ref_h = dh if page_meta['type'] == 'square' else img_resized.height
                            ref_w = dw if page_meta['type'] == 'square' else img_resized.width
                            font_size = int(min(ref_w, ref_h) * 0.05)
                            font = self.get_font(max(font_size, 10))
                            text_bbox = draw.textbbox((0, 0), img_file, font=font)
                            text_w = text_bbox[2] - text_bbox[0]
                            text_h = text_bbox[3] - text_bbox[1]
                            text_x = title_x + (dw - text_w) // 2
                            gap = 8
                            if add_filename == "above":
                                text_y = title_y - text_h - gap
                            elif add_filename == "top":
                                text_y = img_draw_y + gap
                            elif add_filename == "middle":
                                text_y = img_draw_y + (ref_h - text_h) // 2
                            elif add_filename == "bottom":
                                text_y = img_draw_y + ref_h - text_h - gap
                            elif add_filename == "below":
                                text_y = title_y + ref_h + gap
                            # bg设为None，移除衬底
                            filename_draw_info.append({'xy': (text_x, text_y),
                                                       'rect': [text_x - 5, text_y - 2, text_x + text_w + 5,
                                                                text_y + text_h + 2], 'text': img_file, 'font': font,
                                                       'fill': text_color, 'bg': None})

                        cursor_y = title_y + dh + padding
                    except Exception as e:
                        print(f"[Error] a4=1 draw {idx}: {e}")
        else:
            # ================= a4>1 (Multi-Column) Logic =================
            equal_width_mode = draw_mode == "5.equal title width up_down"
            equal_height_mode = draw_mode == "6.equal title height left_right"
            h_diff_title_size = []
            h_title_group_size = []
            title_groups = []
            page_lock_width = w_title_size_int
            w_diff_title_size = []
            w_row_group_size = []
            row_groups = []
            page_lock_height = h_title_size_int
            page_total_occupy_h_local = []  # Local storage for page_total_occupy_h

            # Vertical Centering Calc
            y_offset = 0
            if vertical_offset_mode:
                actual_rows = (len(image_files_page) + n_per_row - 1) // n_per_row
                if title_first_position == "start_from margin":
                    total_title_area_height = actual_rows * w_title_size_int + (actual_rows - 1) * padding
                else:
                    total_title_area_height = actual_rows * w_title_size_int + (actual_rows + 1) * padding
                y_offset = int((height_page_use - total_title_area_height) / 2)
                y_offset = max(y_offset, 0)

            # Horizontal Centering Calc
            x_offset = 0
            mod_int = image_count_in_dir % n_per_row
            if image_count_in_dir < n_per_row:
                x_offset = int(
                    0.5 * (width_page_int - (image_count_in_dir - 1) * padding - image_count_in_dir * w_title_size_int))

            center_offset_x = 0
            x_offset_last_row = 0

            normal_mode = not equal_width_mode and not equal_height_mode
            if normal_mode and vertical_offset_mode:
                total_title_area_width = n_per_row * w_title_size_int + (n_per_row - 1) * padding
                center_offset_x = int((width_page_use - total_title_area_width) / 2)
                # 在垂直居中模式下，更新偏移量
                x_offset_last_row = center_offset_x

            if equal_width_mode:
                h_diff_title_size, h_title_group_size, title_groups, page_lock_width = self.calc_vertical_title_groups(
                    image_files_page, height_page_use, padding, title_first_position, w_title_size_int, n_per_row
                )
                if n_per_row == 1:
                    center_offset_x = int((width_page_use - page_lock_width) / 2)
                elif current_page_group_count > 0 and current_page_group_count < n_per_row:
                    total_group_occupy_width = current_page_group_count * w_title_size_int + (
                            current_page_group_count - 1) * padding
                    center_offset_x = int((width_page_use - total_group_occupy_width) / 2)

            elif equal_height_mode:
                w_diff_title_size, w_row_group_size, row_groups, _, page_total_occupy_h_local, page_lock_height = self.calc_horizontal_row_groups(
                    image_files_page, width_page_use, height_page_use, padding, title_first_position, h_title_size_int,
                    n_per_row
                )
                if n_per_row == 1:
                    center_offset_x = int((width_page_use - page_lock_height) / 2)

                # ========== 修正垂直居中逻辑 ==========
                # 这里的 page_total_occupy_h_local 是针对当前页image_files_page计算出来的列表
                # 它只包含一个元素：当前页的内容高度
                mode6_center_y = 0
                if vertical_offset_mode and len(page_total_occupy_h_local) > 0 and page_total_occupy_h_local[
                    0] < height_page_use:
                    # 修正：使用索引 0，而不是 page_idx-1
                    total_h_current = page_total_occupy_h_local[0]
                    mode6_center_y = int((height_page_use - total_h_current) / 2)
                # ==============================================

            # Drawing Loop
            for idx, img_file in enumerate(image_files_page):
                current_global_idx = global_start_idx + idx
                try:
                    img = Image.open(os.path.join(self.image_dir_full, img_file)).convert('RGB')
                    img_org_w, img_org_h = img.size
                    canvas_x = 0
                    canvas_y = 0
                    resize_w = w_title_size_int
                    resize_h = h_title_size_int
                    img_x = 0
                    img_y = 0
                    canvas_x_int = 0
                    canvas_y_int = 0

                    if equal_width_mode and len(title_groups) > 0:
                        group_idx = -1
                        inner_idx = -1
                        for g_idx, group in enumerate(title_groups):
                            if idx in group:
                                group_idx = g_idx
                                inner_idx = group.index(idx)
                                break
                        if group_idx >= 0:
                            add_offset = padding if title_first_position != "start_from margin" else 0
                            canvas_x = margin + group_idx * (w_title_size_int + padding) + center_offset_x + add_offset
                            group = title_groups[group_idx]
                            inner_y = sum(
                                h_diff_title_size[group[i]] + padding for i in range(inner_idx)) if inner_idx > 0 else 0
                            if vertical_offset_mode:
                                title_group_center_y = int(
                                    margin + (height_page_use - h_title_group_size[group_idx]) / 2)
                                canvas_y = title_group_center_y + inner_y + add_offset
                            else:
                                canvas_y = margin + inner_y + y_offset + add_offset

                            current_h_title = h_diff_title_size[idx]
                            resize_w = page_lock_width if n_per_row == 1 else w_title_size_int
                            resize_h = current_h_title
                            img_ratio = img_org_w / img_org_h
                            resize_h = int(resize_w / img_ratio) if img_ratio != 0 else resize_w
                            img_resized = img.resize((resize_w, resize_h), Image.Resampling.LANCZOS)
                            img_x = int(canvas_x)
                            img_y = int(canvas_y)
                            canvas_x_int = img_x
                            canvas_y_int = img_y

                    elif equal_height_mode and len(row_groups) > 0:
                        row_idx = -1
                        inner_idx = -1
                        for r_idx, row in enumerate(row_groups):
                            if idx in row:
                                row_idx = r_idx
                                inner_idx = row.index(idx)
                                break
                        if row_idx >= 0:
                            add_offset = padding if title_first_position != "start_from margin" else 0

                            canvas_y = margin + mode6_center_y + row_idx * (page_lock_height + padding) + add_offset
                            inner_x = sum(
                                w_diff_title_size[row[i]] + padding for i in range(inner_idx)) if inner_idx > 0 else 0
                            row_center_x = int((width_page_use - w_row_group_size[row_idx]) / 2)
                            canvas_x = margin - add_offset + row_center_x + inner_x + center_offset_x + padding

                            current_w_title = w_diff_title_size[idx]
                            resize_w = current_w_title
                            resize_h = page_lock_height
                            img_ratio = img_org_w / img_org_h
                            resize_w = int(resize_h * img_ratio) if img_ratio != 0 else resize_h
                            img_resized = img.resize((resize_w, resize_h), Image.Resampling.LANCZOS)
                            img_x = int(canvas_x)
                            img_y = int(canvas_y)
                            canvas_x_int = img_x
                            canvas_y_int = img_y

                    else:
                        col = idx % n_per_row
                        row = idx // n_per_row
                        idx_total = idx + (page_num - 1) * n_per_row * n_per_col_int
                        if title_first_position == "start_from margin":
                            canvas_x = margin + col * (w_title_size_int + padding)
                            canvas_y = margin + row * (w_title_size_int + padding) + y_offset
                        elif title_first_position in ["start_from margin + padding",
                                                      "start_from margin + padding(vertical centering)"]:
                            canvas_x = margin + padding + col * (w_title_size_int + padding)
                            canvas_y = margin + padding + row * (w_title_size_int + padding) + y_offset

                        # ========== 修正：末行居中逻辑 ==========
                        remaining_images = image_count_in_dir - idx_total
                        is_last_row = remaining_images > 0 and remaining_images <= n_per_row
                        is_incomplete_row = remaining_images > 0 and remaining_images < n_per_row

                        if col == 0 and is_last_row and is_incomplete_row:
                            # 计算最后一行未使用的水平宽度，均分到左右两边
                            total_row_width = remaining_images * w_title_size_int + (remaining_images - 1) * padding
                            # 修正：使用 width_page_use (可用宽度) 而不是 width_page_int (总宽度)
                            # 这样可以正确对齐到有效内容区域的中心，而不是偏移一个 margin
                            unused_width = width_page_use - total_row_width
                            x_offset_last_row = unused_width // 2
                        # ==================================================

                        canvas_x_int = int(canvas_x) + x_offset + x_offset_last_row
                        canvas_y_int = int(canvas_y)
                        resize_w = w_title_size_int
                        resize_h = w_title_size_int

                        if draw_mode == "2.Stretches image to fill":
                            img_resized = img.resize((resize_w, resize_h), Image.Resampling.LANCZOS)
                            img_x, img_y = canvas_x_int, canvas_y_int
                        elif draw_mode == "1.smaller value filler":
                            ls = max(img.width, img.height)
                            sb = min(ls, resize_w)
                            s = sb / ls
                            nw = int(img.width * s);
                            nh = int(img.height * s)
                            img_resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
                            img_x = canvas_x_int + (resize_w - nw) // 2
                            img_y = canvas_y_int + (resize_h - nh) // 2
                        elif draw_mode == "3.zoom by long side (recommended)":
                            ls = max(img.width, img.height)
                            s = resize_w / ls
                            nw = int(img.width * s);
                            nh = int(img.height * s)
                            img_resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
                            img_x = canvas_x_int + (resize_w - nw) // 2
                            img_y = canvas_y_int + (resize_h - nh) // 2
                        elif draw_mode == "4.crop square by short side":
                            img_sq = self.crop_center_square(img)
                            img_resized = img_sq.resize((resize_w, resize_h), Image.Resampling.LANCZOS)
                            img_x, img_y = canvas_x_int, canvas_y_int
                        else:
                            img_resized = img.resize((resize_w, resize_h), Image.Resampling.LANCZOS)
                            img_x, img_y = canvas_x_int, canvas_y_int
                        # print(f'Page{page_num}, canvas_x_int={canvas_x_int}, canvas_y_int={canvas_y_int}，'
                        #       f'idx={idx+1},n_per_row={n_per_row}')
                    # Paste
                    # Save Logic
                    if save_mode != "none":
                        self.save_single_title(img_resized, title_border, title_border_style,
                                               titles_save_dir, img_file, add_filename, filename_color,
                                               "title" if save_mode == "save single title" else "image",
                                               save_filename_mode, page_num, idx, current_global_idx,
                                               resize_w, resize_h, background_style=background_style)

                    if img_resized.mode == 'RGB' and img_mode == 'RGBA':
                        img_resized = img_resized.convert('RGBA')
                        alpha_layer = Image.new('L', img_resized.size, 255)
                        img_resized.putalpha(alpha_layer)

                    mask = img_resized.split()[-1] if img_mode == 'RGBA' else None
                    img_x = max(0, min(img_x, width_page_int - img_resized.width))
                    # img_y = max(0, min(img_y, height_page_int - img_resized.height))
                    concat.paste(img_resized, (img_x, img_y), mask=mask)

                    # Border
                    if title_border != "None":
                        ref_w = resize_w if not (equal_width_mode or equal_height_mode) else (
                            resize_w if equal_width_mode else w_diff_title_size[idx])
                        ref_h = resize_h if not (equal_width_mode or equal_height_mode) else (
                            resize_h if equal_width_mode else resize_h)

                        bx = canvas_x_int
                        by = canvas_y_int
                        if equal_height_mode:
                            bx = img_x

                        rect = [bx, by, bx + ref_w, by + ref_h]
                        if "Rounded" in title_border:
                            self.draw_dashed_rounded_rectangle_manual(draw, rect, 10, dash_title, 2, border_color)
                        else:
                            self.draw_dashed_rectangle_manual(draw, rect, dash_title, 2, border_color)

                    # Filename Queue
                    if add_filename != "none":
                        text_color = filename_color

                        # 计算 X 轴参考宽度
                        ref_w = resize_w
                        if equal_height_mode:
                            ref_w = img_resized.width

                        # 计算 Y 轴参考高度
                        # 修正核心：始终基于 title 的高度 (resize_h) 和 title 的顶部 (canvas_y_int) 进行定位
                        ref_h = resize_h

                        font_size = int(min(ref_w, ref_h) * 0.05)
                        font = self.get_font(max(font_size, 10))
                        text_bbox = draw.textbbox((0, 0), img_file, font=font)
                        text_w = text_bbox[2] - text_bbox[0]
                        text_h = text_bbox[3] - text_bbox[1]

                        # X轴居中
                        text_x = canvas_x_int + (ref_w - text_w) // 2

                        gap = 8

                        # Y轴定位逻辑修正：全部基于 canvas_y_int (title顶部) 和 resize_h (title高度)
                        if add_filename == "above":
                            text_y = canvas_y_int - text_h - gap
                        elif add_filename == "top":
                            # 修正：原代码使用 img_y (图片顶部)，现改为 canvas_y_int (title顶部)
                            text_y = canvas_y_int + gap
                        elif add_filename == "middle":
                            # 修正：原代码基于 img_y 偏移，现改为基于 title 垂直居中
                            text_y = canvas_y_int + (resize_h - text_h) // 2
                        elif add_filename == "bottom":
                            # 修正：原代码基于 img_y 偏移，现改为基于 title 底部
                            text_y = canvas_y_int + resize_h - text_h - gap
                        elif add_filename == "below":
                            text_y = canvas_y_int + resize_h + gap
                        # bg设为None，移除衬底
                        filename_draw_info.append({'xy': (text_x, text_y),
                                                   'rect': [text_x - 5, text_y - 2, text_x + text_w + 5,
                                                            text_y + text_h + 2], 'text': img_file, 'font': font,
                                                   'fill': text_color, 'bg': None})


                except Exception as e:
                    print(f"[Error] draw {idx}: {e}")

        if page_border != "None":
            full_rect = [margin, margin, width_page_int - margin, height_page_int - margin]
            if "Rounded" in page_border:
                self.draw_dashed_rounded_rectangle_manual(draw, full_rect, 10, dash_page, 2, border_color)
            else:
                self.draw_dashed_rectangle_manual(draw, full_rect, dash_page, 2, border_color)

        # Draw Filename
        for info in filename_draw_info:
            if info['bg'] is not None:
                draw.rectangle(info['rect'], fill=info['bg'])
            draw.text(info['xy'], info['text'], font=info['font'], fill=info['fill'])

        if img_mode == 'RGBA':
            concat_np = np.array(concat).astype(np.float32) / 255.0
        else:
            concat_np = np.array(concat).astype(np.float32) / 255.0
            if len(concat_np.shape) == 2:
                concat_np = np.repeat(np.expand_dims(concat_np, -1), 3, -1)
        return concat_np

    def generate_concat(self, a1_image_dir, a2_page_width, a3_page_aspect_ratio, a4_cols_rows_per_page, a5_page_margin,
                        a6_title_padding,
                        a8_title_first_position, a7_title_draw_mode, a10_title_border, a11_title_border_style,
                        a12_page_border, a13_page_border_style, a97_title_save_mode, a98_title_save_dir,
                        a99_title_save_filename,
                        a9_background_style, a14_filename_position, a15_filename_color):

        self.image_dir_full = a1_image_dir
        self.width_page_use_global = a2_page_width - 2 * a5_page_margin

        # 1. 处理新功能：获取文件名颜色
        filename_color_rgb = self.get_filename_color_by_name(a15_filename_color)

        titles_final_path = ""
        if a97_title_save_mode != "none":
            mode_suffix = ""
            if a97_title_save_mode == "save single title":
                mode_suffix = "(1)"
            elif a97_title_save_mode == "save single image":
                mode_suffix = "(2)"
            # =================================================

            # 如果勾选保存，计算带时间戳的路径（包含模式后缀）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # 拼接路径格式：.../concat_titles(1)_20250117_123045
            titles_final_path = os.path.join(a98_title_save_dir, f"concat_titles{mode_suffix}_{timestamp}").replace(
                "\\", "/")
            os.makedirs(titles_final_path, exist_ok=True)
        else:
            # 如果未勾选，输出英文提示
            titles_final_path = "can't display `b5_title_save_path` due to `a97_title_save_mode` is 'none'"

        if not os.path.exists(a1_image_dir):
            print(f"[Error] 图片文件夹不存在: {a1_image_dir}")
            error_img = np.zeros((1, 100, 100, 3), dtype=np.float32)
            error_img[:, :, :, 0] = 1.0
            return (torch.from_numpy(error_img), 0, "0×0", 0, titles_final_path, self.get_node_tips())

        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp')
        image_files = [f for f in os.listdir(a1_image_dir) if f.lower().endswith(image_extensions)]
        image_count_in_dir = len(image_files)

        if image_count_in_dir == 0:
            print("[Error] 文件夹内无有效图片")
            error_img = np.zeros((1, 100, 100, 3), dtype=np.float32)
            error_img[:, :, :, 0] = 1.0
            error_img[:, :, :, 1] = 1.0
            return (torch.from_numpy(error_img), 0, "0×0", 0, titles_final_path, self.get_node_tips())

        title_ratio = round(self.convert_ratio_to_float(a3_page_aspect_ratio), 2)
        height_page = int(a2_page_width / title_ratio)
        print(f"[✅] 画布尺寸: {a2_page_width} × {height_page} | 宽高比: {a3_page_aspect_ratio}")

        width_page_use = a2_page_width - 2 * a5_page_margin
        height_page_use = height_page - 2 * a5_page_margin

        is_a4_equals_1 = (a4_cols_rows_per_page == 1)
        is_start_from_margin = (a8_title_first_position == "start_from margin")
        has_outer_padding = (not is_start_from_margin)
        is_vert_center = (a8_title_first_position == "start_from margin + padding(vertical centering)")

        # ========== 关键修正：变量前置初始化 ==========
        equal_width_mode = a7_title_draw_mode == "5.equal title width up_down"
        equal_height_mode = a7_title_draw_mode == "6.equal title height left_right"
        page_group_count = {}
        page_total_occupy_height = []
        page_image_mapping = {}
        page_data_list = []
        w_title_size = 100
        h_title_size = 100
        wh_per_title = ""
        n_per_col_actual = 1  # 新增：用于存储实际计算出的每页行数
        # ================================================

        if is_a4_equals_1:
            # ========== a4=1 (单列) 逻辑 ==========
            page_data_list = self.calc_vertical_title_groups_a4_1(
                image_files, width_page_use, height_page_use,
                a6_title_padding, a8_title_first_position, a7_title_draw_mode
            )
            # 填充分页信息
            for i in range(len(page_data_list)):
                page_group_count[i] = 1
                page_total_occupy_height.append(height_page_use)
                page_image_mapping[i] = page_data_list[i]['files']

            m = page_data_list[0]['meta'] if page_data_list else {}
            if m.get('type') == 'square':
                # 修复：同时定义 int 类型变量，供后续 wh_per_title 使用
                w_title_size_int = m['size']
                h_title_size_int = m['size']
                w_title_size = w_title_size_int
                h_title_size = h_title_size_int
                wh_per_title = f"title width = {w_title_size_int}\nequal title height = {h_title_size_int}"
            elif m.get('type') == 'fixed_width':
                w_title_size_int = m['width']
                h_title_size_int = m['width']  # 传宽高相同，函数内重新计算h
                w_title_size = w_title_size_int
                h_title_size = w_title_size_int  # 保持变量一致
                wh_per_title = f"equal title width = {w_title_size_int}"
            elif m.get('type') == 'fixed_height':
                w_title_size_int = m['height']  # 传高宽相同，函数内重新计算w
                h_title_size_int = m['height']
                w_title_size = h_title_size_int
                h_title_size = h_title_size_int
                wh_per_title = f"equal title height = {h_title_size_int}"
            else:
                # 兜底逻辑
                w_title_size = 100
                h_title_size = 100
                w_title_size_int = 100
                h_title_size_int = 100
                wh_per_title = f"{w_title_size_int}×{h_title_size_int}"

        else:
            # ========== a4>1 (多列) 逻辑 ==========
            if is_start_from_margin:
                w_title_size = (width_page_use - (a4_cols_rows_per_page - 1) * a6_title_padding) / a4_cols_rows_per_page
            else:
                w_title_size = (width_page_use - (a4_cols_rows_per_page + 1) * a6_title_padding) / a4_cols_rows_per_page

            w_title_size_int = int(w_title_size)

            if a7_title_draw_mode in ["1.smaller value filler", "2.Stretches image to fill",
                                      "3.zoom by long side (recommended)", "4.crop square by short side"]:
                h_title_size_int = w_title_size_int
            else:
                h_title_size_int = max(1, int(w_title_size / self.convert_ratio_to_float(a3_page_aspect_ratio)))

            # 修复：确保 h_title_size 赋值为正确的整数，否则传递给 create_single_concat_page 时可能是初始值 100
            h_title_size = h_title_size_int

            if equal_width_mode:
                _, _, all_title_groups, _ = self.calc_vertical_title_groups(image_files, height_page_use,
                                                                            a6_title_padding,
                                                                            a8_title_first_position, w_title_size_int,
                                                                            a4_cols_rows_per_page)
                total_groups = len(all_title_groups)
                groups_per_page = a4_cols_rows_per_page
                total_pages = (total_groups + groups_per_page - 1) // groups_per_page if total_groups > 0 else 1
                for page_idx in range(total_pages):
                    start_g = page_idx * groups_per_page
                    end_g = min(start_g + groups_per_page, total_groups)
                    page_groups = all_title_groups[start_g:end_g]
                    page_images = []
                    for g in page_groups: page_images.extend(g)
                    page_image_mapping[page_idx] = page_images
                    page_group_count[page_idx] = len(page_groups)
                    page_total_occupy_height.append(height_page_use)
                wh_per_title = f"equal title width = {w_title_size_int}"
            elif equal_height_mode:
                _, _, row_groups, page_row_mapping, page_total_occupy_height_calc, _ = self.calc_horizontal_row_groups(
                    image_files, width_page_use, height_page_use, a6_title_padding, a8_title_first_position,
                    h_title_size_int,
                    a4_cols_rows_per_page
                )
                total_pages = len(page_row_mapping)
                page_total_occupy_height = page_total_occupy_height_calc
                for page_idx in range(total_pages):
                    page_rows = page_row_mapping[page_idx]
                    page_images = []
                    for r in page_rows: page_images.extend(r)
                    page_image_mapping[page_idx] = page_images
                    page_group_count[page_idx] = len(page_rows)
                    # page_total_occupy_height 已在上方赋值为 list
                wh_per_title = f"equal title height = {h_title_size_int}"
            else:
                # 模式1-4 段通网格
                n_per_col = 1
                for n in range(100, 0, -1):
                    h_sum = n * h_title_size_int + (n - 1) * a6_title_padding
                    if has_outer_padding:
                        h_sum += (n + 1) * a6_title_padding
                    if h_sum <= height_page_use:
                        n_per_col = n
                        break
                if n_per_col == 0: n_per_col = 1
                n_per_col_actual = n_per_col  # 保存实际行数

                titles_per_page = a4_cols_rows_per_page * n_per_col
                image_pages = [image_files[i:i + titles_per_page] for i in range(0, len(image_files), titles_per_page)]
                total_pages = len(image_pages)
                for page_idx in range(total_pages):
                    page_image_mapping[page_idx] = image_pages[page_idx]
                    page_group_count[page_idx] = 1
                    page_total_occupy_height.append(height_page_use)

                wh_per_title = f"title width = {w_title_size_int}\nequal title height = {h_title_size_int}"

        print(
            f"[✅分页信息] 模式: {a7_title_draw_mode} | 通用队列数: {a4_cols_rows_per_page} | 总页数: {len(page_image_mapping)} | 块尺寸: {wh_per_title}")

        all_concats = []
        vertical_offset_mode = a8_title_first_position == "start_from margin + padding(vertical centering)"

        # 关键修正：循环遍历 page_image_mapping，而不是 page_data_list，确保索引兼容
        for page_idx in range(len(page_image_mapping)):
            current_page_num = page_idx + 1

            # 计算全局索引起始值
            global_start_idx = 0
            for i in range(page_idx):
                global_start_idx += len(page_image_mapping[i])

            # 安全获取分页数据
            current_group_cnt = page_group_count.get(page_idx, 1)
            current_page_h = page_total_occupy_height[page_idx] if page_idx < len(
                page_total_occupy_height) else height_page_use

            # 获取文件列表
            if isinstance(page_image_mapping[page_idx][0], int):
                page_image_files = [image_files[idx] for idx in page_image_mapping[page_idx]]
            else:
                page_image_files = page_image_mapping[page_idx]

            print(
                f"\n{'=' * 50} 绘制第 {current_page_num}/{len(page_image_mapping)} 页 (块组数: {current_group_cnt}) {'=' * 50}")

            # 计算 n_per_col 参数
            n_per_col_arg = 1
            if not equal_height_mode and not equal_width_mode:
                # 修正：直接使用前面计算出的实际行数，而不是错误的除法公式
                n_per_col_arg = n_per_col_actual
            elif equal_height_mode:
                n_per_col_arg = 9999  # 哑牌值，防止除零

            concat_page_np = self.create_single_concat_page(
                page_image_files, a2_page_width, height_page, a4_cols_rows_per_page,
                n_per_col_arg,
                a5_page_margin, a6_title_padding, a8_title_first_position,
                w_title_size, h_title_size, a7_title_draw_mode, a10_title_border, a11_title_border_style,
                a12_page_border, a13_page_border_style, current_page_num,
                a97_title_save_mode, titles_final_path, a99_title_save_filename, global_start_idx,
                a9_background_style,
                vertical_offset_mode, image_count_in_dir,
                current_page_group_count=current_group_cnt,
                page_total_occupy_h=current_page_h,
                add_filename=a14_filename_position,
                filename_color=filename_color_rgb,  # 新增：传入颜色
                page_meta=page_data_list[page_idx]['meta'] if is_a4_equals_1 and page_idx < len(
                    page_data_list) else None
            )
            all_concats.append(concat_page_np)

        concat_np = np.stack(all_concats, axis=0) if all_concats else np.zeros((1, 100, 100, 3), dtype=np.float32)
        concat_tensor = torch.from_numpy(concat_np)
        return (concat_tensor, len(page_image_mapping), wh_per_title, image_count_in_dir, titles_final_path,
                self.get_node_tips())


NODE_CLASS_MAPPINGS["ImageConcatNode"] = ImageConcatNode
NODE_DISPLAY_NAME_MAPPINGS["ImageConcatNode"] = "Image concatenate(V1.1 QQ2540968810)"

if __name__ == "__main__":
    print("✅ Comfyui-Image-Concat(V1.1) Registration successful!")
