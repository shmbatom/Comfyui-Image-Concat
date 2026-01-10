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
    """A Powerful Image concat Node:✅Multiple Image-block Fill Modes + Light/Dark/Transparent + Save Each Block"""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "a1_image_dir": ("STRING", {"default": "", "placeholder": "Path to image folder"}),
                "a2_width_page": ("INT", {"default": 4000, "min": 100, "max": 50000, "step": 10}),
                "a3_aspect_ratio": ("COMBO", {
                    "default": "3:2",
                    "forceInput": False,
                    "options": ["1:1", "3:2", "4:3", "16:9", "2:3", "3:4", "9:16"]
                }),
                "a4_n_per_row": ("INT", {"default": 3, "min": 1, "max": 20, "step": 1}),
                "a5_margin": ("INT", {"default": 50, "min": 0, "max": 500, "step": 10}),
                "a6_spacing": ("INT", {"default": 30, "min": 0, "max": 200, "step": 1}),
                # ========== 核心新增：第一个区块起始位置控制 ==========
                "a7_block_first_position": ("COMBO", {
                    "default": "start_from margin",
                    "forceInput": False,
                    "options": [
                        "start_from margin",
                        "start_from margin + spacing",
                        "start_from margin + spacing(vertical centering)"
                    ]
                }),
                # ==================================================
                "a8_draw_mode": ("COMBO", {
                    "default": "3.zoom Long side(recommend)",
                    "forceInput": False,
                    "options": [
                        "1.smaller value filler",
                        "2.Stretches image to fill",
                        "3.zoom Long side(recommend)",
                        "4.crop square by short side"
                    ]
                }),
                "a9_block_border": ("COMBO", {
                    "default": "Rounded (radius 10)",
                    "forceInput": False,
                    "options": ["None", "Rectangle", "Rounded (radius 10)", "Rounded (radius 20)"]
                }),
                "a10_block_border_style": ("COMBO", {
                    "default": "Solid",
                    "forceInput": False,
                    "options": ["Solid", "Dashed (4,4)", "Dashed (8,8)", "Dotted (1,2)", "Dash-dot (8,4,2,4)"]
                }),
                "a11_page_border": ("COMBO", {
                    "default": "Rounded (radius 30)",
                    "forceInput": False,
                    "options": ["None", "Rectangle", "Rounded (radius 10)", "Rounded (radius 20)",
                                "Rounded (radius 30)"]
                }),
                "a12_page_border_style": ("COMBO", {
                    "default": "Solid",
                    "forceInput": False,
                    "options": ["Solid", "Dashed (4,4)", "Dashed (8,8)", "Dotted (1,2)", "Dash-dot (8,4,2,4)"]
                }),
                "a13_save_blocks": ("BOOLEAN", {"default": True, "label": "Save individual block images"}),
                "a14_blocks_save_dir": (
                    "STRING", {"default": "./output/concat_blocks", "placeholder": "Block save directory path"}),
                "a15_background_style": ("COMBO", {
                    "default": "Light (white)",
                    "forceInput": False,
                    "options": ["Light (white)", "Dark (black)", "Transparent (alpha channel)"]
                }),
            },
            "optional": {},
        }

    RETURN_TYPES = ("IMAGE", "INT", "STRING", "INT", "STRING", "STRING")
    RETURN_NAMES = ("b1_concat_images", "b2.page_count", "b3_wh_per_block", "b4_image_count_in_dir", "b5_blocks_save_path", "b6_tips")
    FUNCTION = "generate_concat"
    CATEGORY = "Image Processing/concat"
    DESCRIPTION = "A Powerful Image concat Node: \nMultiple Image-block Fill Modes + Light/Dark/Transparent + Save Each Block"

    def convert_ratio_to_float(self, ratio_str):
        try:
            width_part, height_part = ratio_str.split(":")
            width_num = float(width_part)
            height_num = float(height_part)
            return width_num / height_num
        except (ValueError, IndexError) as e:
            print(f"[Warning] Invalid ratio format: {ratio_str}, using default 1.5 (3:2)")
            return 1.5

    def get_dash_pattern(self, style_name):
        print(f"\n[Debug] Parsing style name: {style_name}")
        if style_name == "Solid":
            dash_pattern = None
        elif style_name == "Dashed (4,4)":
            dash_pattern = (4, 4)
        elif style_name == "Dashed (8,8)":
            dash_pattern = (8, 8)
        elif style_name == "Dotted (1,2)":
            dash_pattern = (1, 2)
        elif style_name == "Dash-dot (8,4,2,4)":
            dash_pattern = (8, 4, 2, 4)
        else:
            dash_pattern = None
        print(f"[Debug] Parsing result: {dash_pattern}")
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
                draw.line([(x1 + ux * current_pos, y1 + uy * current_pos),
                           (seg_end_x, seg_end_y)], fill=color, width=width)
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

    def save_single_block(self, img_resized, block_border, block_border_style,
                          save_path, w_block, h_block, border_width=2, background_style="Light (white)"):
        bg_color, img_mode = self.get_background_config(background_style)
        border_color = self.get_border_color(background_style)

        block_canvas = Image.new(img_mode, (int(w_block), int(h_block)), color=bg_color)
        img_x = (int(w_block) - img_resized.width) // 2
        img_y = (int(h_block) - img_resized.height) // 2

        if img_resized.mode == 'RGB' and img_mode == 'RGBA':
            img_resized = img_resized.convert('RGBA')
            alpha_layer = Image.new('L', img_resized.size, 255)
            img_resized.putalpha(alpha_layer)

        mask = img_resized.split()[-1] if img_mode == 'RGBA' else None
        block_canvas.paste(img_resized, (img_x, img_y), mask=mask)

        if block_border != "None":
            draw = ImageDraw.Draw(block_canvas)
            dash_pattern = self.get_dash_pattern(block_border_style)
            border_rect = [0, 0, int(w_block), int(h_block)]

            if "Rounded" in block_border:
                radius = 10 if "10" in block_border else 20
                self.draw_dashed_rounded_rectangle_manual(
                    draw, border_rect, radius, dash_pattern,
                    border_width, color=border_color
                )
            else:
                self.draw_dashed_rectangle_manual(
                    draw, border_rect, dash_pattern,
                    border_width, color=border_color
                )
        block_canvas.save(save_path, 'PNG', quality=100, pnginfo=None, optimize=False)
        print(f"[Save] Block saved with Alpha: {save_path}")

    def create_single_concat_page(self, image_files_page, width_page, height_page, n_per_row, n_per_col_int,
                                  margin, spacing, block_first_position,
                                  w_block_size, h_block_size, draw_mode, block_border, block_border_style,
                                  page_border, page_border_style, page_num,
                                  save_blocks, blocks_save_dir, background_style, vertical_offset_mode, image_count_in_dir):
        width_page_int = int(round(width_page))
        height_page_int = int(round(height_page))
        w_block_size_int = int(round(w_block_size))
        h_block_size_int = int(round(h_block_size))

        bg_color, img_mode = self.get_background_config(background_style)
        border_color = self.get_border_color(background_style)

        concat = Image.new(img_mode, (width_page_int, height_page_int), color=bg_color)
        draw = ImageDraw.Draw(concat)

        print(
            f"\n[Debug] Page {page_num} - BG Style: {background_style} | Mode: {img_mode} | Border Color: {border_color} | Block Start: {block_first_position}")
        dash_block = self.get_dash_pattern(block_border_style)
        dash_page = self.get_dash_pattern(page_border_style)

        # ========== 纵向居中逻辑：仅在 vertical_offset_mode 为 True 时生效 ==========
        y_offset = 0  # 默认无偏移
        if vertical_offset_mode:
            actual_rows = (len(image_files_page) + n_per_row - 1) // n_per_row
            print(f"[Debug] Page {page_num} - Actual rows: {actual_rows} (total imgs: {len(image_files_page)})")

            # 计算当前页block区域总高度（适配起始位置）
            if block_first_position == "start_from margin":
                total_block_area_height = actual_rows * h_block_size + (actual_rows - 1) * spacing
            elif block_first_position in ["start_from margin + spacing",
                                          "start_from margin + spacing(vertical centering)"]:
                total_block_area_height = actual_rows * h_block_size + (actual_rows + 1) * spacing
            # 垂直居中偏移量
            height_page_use = height_page - 2 * margin
            y_offset = int((height_page_use - total_block_area_height) / 2)
            y_offset = max(y_offset, 0)
            print(f"[Debug] Page {page_num} - Total block area height: {total_block_area_height}, Y offset: {y_offset}")
        # ==========================================================================

        num_rows_page = (len(image_files_page) + n_per_row - 1) // n_per_row

        if save_blocks:
            page_block_dir = os.path.join(blocks_save_dir, f"page_{page_num}")
            os.makedirs(page_block_dir, exist_ok=True)

        x_offset = 0
        mod_int = image_count_in_dir % n_per_row

        if image_count_in_dir < n_per_row:
            x_offset = int(0.5*(width_page_int - (image_count_in_dir - 1) * spacing - image_count_in_dir * w_block_size_int))
            print(f"[✅] Total valid images: {image_count_in_dir}, 余数{mod_int}, 左右偏移{x_offset}")

        x_offset_last_row = 0
        idx_total = 0
        for idx, img_file in enumerate(image_files_page):
            try:
                img_path = os.path.join(self.image_dir_full, img_file)
                img = Image.open(img_path).convert('RGB')

                col = idx % n_per_row
                row = idx // n_per_row

                # ========== 核心适配：基础坐标 + 纵向偏移（仅指定模式生效） ==========
                if block_first_position == "start_from margin":
                    canvas_x = margin + col * (w_block_size + spacing)
                    canvas_y = margin + row * (h_block_size + spacing) + y_offset  # 加偏移
                elif block_first_position in ["start_from margin + spacing",
                                              "start_from margin + spacing(vertical centering)"]:
                    canvas_x = margin + spacing + col * (w_block_size + spacing)
                    canvas_y = margin + spacing + row * (h_block_size + spacing) + y_offset  # 加偏移
                # ==============================================================
                idx_total = idx + (page_num - 1) * n_per_row * n_per_col_int
                if image_count_in_dir - idx_total == mod_int and idx_total + 1 > n_per_row:
                   if mod_int > 0:
                       x_offset_last_row = int(0.5*(width_page_int - (mod_int - 1) * spacing - mod_int * w_block_size_int))-int(canvas_x)

                print(f"[✅] 正处理: {idx_total + 1}/{image_count_in_dir}, 余数{mod_int}, 左右偏移{x_offset}, 末行左右偏移{x_offset_last_row}")
                canvas_x_int = int(canvas_x) + x_offset + x_offset_last_row
                canvas_y_int = int(canvas_y)

                if draw_mode == "2.Stretches image to fill":
                    img_resized = img.resize((w_block_size_int, h_block_size_int), Image.Resampling.LANCZOS)
                    img_x, img_y = canvas_x_int, canvas_y_int

                elif draw_mode == "1.smaller value filler":
                    img.thumbnail((w_block_size_int, h_block_size_int), Image.Resampling.LANCZOS)
                    img_x = canvas_x_int + (w_block_size_int - img.width) // 2
                    img_y = canvas_y_int + (h_block_size_int - img.height) // 2
                    img_resized = img

                elif draw_mode == "3.zoom Long side(recommend)":
                    img_w, img_h = img.size
                    long_side = max(img_w, img_h)
                    target_long_side = w_block_size_int

                    if long_side < target_long_side:
                        scale_ratio = target_long_side / long_side
                        new_w = int(img_w * scale_ratio)
                        new_h = int(img_h * scale_ratio)
                        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    else:
                        img.thumbnail((w_block_size_int, h_block_size_int), Image.Resampling.LANCZOS)
                        img_resized = img

                    img_x = canvas_x_int + (w_block_size_int - img_resized.width) // 2
                    img_y = canvas_y_int + (h_block_size_int - img_resized.height) // 2

                elif draw_mode == "4.crop square by short side":
                    img_square = self.crop_center_square(img)
                    img_resized = img_square.resize((w_block_size_int, h_block_size_int), Image.Resampling.LANCZOS)
                    img_x, img_y = canvas_x_int, canvas_y_int

                if save_blocks:
                    img_name = os.path.splitext(img_file)[0]
                    block_save_path = os.path.join(page_block_dir, f"block_{page_num}_{idx + 1}_{img_name}.png")
                    self.save_single_block(img_resized, block_border, block_border_style,
                                           block_save_path, w_block_size, h_block_size,
                                           background_style=background_style)

                if img_resized.mode == 'RGB' and img_mode == 'RGBA':
                    img_resized = img_resized.convert('RGBA')
                    alpha_layer = Image.new('L', img_resized.size, 255)
                    img_resized.putalpha(alpha_layer)
                mask = img_resized.split()[-1] if img_mode == 'RGBA' else None
                concat.paste(img_resized, (img_x, img_y), mask=mask)

                if block_border != "None":
                    border_rect = [
                        canvas_x_int, canvas_y_int,
                        canvas_x_int + w_block_size_int,
                        canvas_y_int + h_block_size_int
                    ]
                    border_width = 2

                    if "Rounded" in block_border:
                        radius = 10 if "10" in block_border else 20
                        self.draw_dashed_rounded_rectangle_manual(
                            draw, border_rect, radius, dash_block,
                            border_width, color=border_color
                        )
                    else:
                        self.draw_dashed_rectangle_manual(
                            draw, border_rect, dash_block,
                            border_width, color=border_color
                        )

            except Exception as e:
                print(f"[Error] Page {page_num} - Failed to process {img_file}: {str(e)}")
                continue

        if page_border != "None":
            width_page_use = width_page_int - 2 * margin
            height_page_use = height_page_int - 2 * margin
            full_rect = [margin, margin, margin + width_page_use, margin + height_page_use]
            border_width = 4

            if "Rounded" in page_border:
                radius_map = {"10": 10, "20": 20, "30": 30}
                radius = radius_map.get(page_border.replace("Rounded (radius ", "").replace(")", ""), 10)
                self.draw_dashed_rounded_rectangle_manual(draw, full_rect, radius, dash_page, border_width,
                                                          border_color)
            else:
                self.draw_dashed_rectangle_manual(draw, full_rect, dash_page, border_width, border_color)

        if img_mode == 'RGBA':
            concat_np = np.array(concat).astype(np.float32) / 255.0
        else:
            concat_np = np.array(concat).astype(np.float32) / 255.0
            if len(concat_np.shape) == 2 or concat_np.shape[-1] == 1:
                concat_np = np.repeat(np.expand_dims(concat_np, -1), 3, -1)

        return concat_np

    def get_node_tips(self):
        tips = """
# ✅ Perfect Image concat Node (True Alpha Channel)
## Core Feature: Transparent Background + Block Start Position Control
✅ Export PNG with **4 full channels (R/G/B/A)** in Photoshop\n
✅ All blank area (margin/spacing/empty) = Alpha=0 (pure transparent)\n
✅ Only image content + border lines = Alpha=255 (opaque)\n
✅ Three block start position options: \n
   - start_from margin 
   - start_from margin + spacing(top align)
   - start_from margin + spacing(vertical centering)\n
✅ Auto calculate block size for different start positions (Horizontal + Vertical)\n
✅ Saved individual blocks also have complete Alpha channel\n

## Input Params Tips
- block_first_position: start_from margin → block size = (use_w - (n-1)*spacing)/n | row height = (use_h - (n-1)*spacing)/n
- block_first_position: start_from margin + spacing(top align) → block size = (use_w - (n+1)*spacing)/n | row height = (use_h - (n+1)*spacing)/n
- block_first_position: start_from margin + spacing(vertical centering) → same as top align + vertical center offset
        """
        return tips.strip()

    def generate_concat(self, a1_image_dir, a2_width_page, a3_aspect_ratio, a4_n_per_row, a5_margin, a6_spacing,
                        a7_block_first_position, a8_draw_mode, a9_block_border, a10_block_border_style,
                        a11_page_border, a12_page_border_style, a13_save_blocks, a14_blocks_save_dir, a15_background_style):
        print("\n" + "=" * 60)
        print("[✅Image_Concat_Node] Start generating concat images (Block Start Position + True Alpha Channel)")
        print(f"[✅] Selected Background: {a15_background_style} | Block Start: {a7_block_first_position}")
        print("=" * 60)

        self.image_dir_full = a1_image_dir
        blocks_final_path = ""
        if a13_save_blocks:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blocks_final_path = os.path.join(a14_blocks_save_dir, f"concat_blocks_{timestamp}")
            os.makedirs(blocks_final_path, exist_ok=True)
            print(f"[✅] Block save path: {blocks_final_path}")

        if not os.path.exists(a1_image_dir):
            print(f"[Error] Folder not exist: {a1_image_dir}")
            error_img = np.zeros((1, 100, 100, 3), dtype=np.float32)
            error_img[:, :, :, 0] = 1.0
            tips = self.get_node_tips()
            return (torch.from_numpy(error_img), 0, "0×0", 0, blocks_final_path, tips)

        image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
        image_files = [f for f in os.listdir(a1_image_dir) if f.lower().endswith(image_extensions)]
        image_count_in_dir = len(image_files)
        print(f"[✅] Found valid images: {image_count_in_dir}")

        if image_count_in_dir == 0:
            print("[Error] No image files in folder")
            error_img = np.zeros((1, 100, 100, 3), dtype=np.float32)
            error_img[:, :, :, 0] = 1.0
            error_img[:, :, :, 1] = 1.0
            tips = self.get_node_tips()
            return (torch.from_numpy(error_img), 0, "0×0", 0, blocks_final_path, tips)

        block_ratio = round(self.convert_ratio_to_float(a3_aspect_ratio), 2)
        height_page = int(a2_width_page / block_ratio)
        print(f"[✅] Aspect Ratio: {a3_aspect_ratio} → {block_ratio:.2f} | Canvas Size: {a2_width_page} × {height_page}")

        width_page_use = a2_width_page - 2 * a5_margin
        height_page_use = height_page - 2 * a5_margin

        # ========== 核心公式：水平宽度 - 根据起始位置自动计算 ==========
        if a7_block_first_position == "start_from margin":
            w_block_size = (width_page_use - (a4_n_per_row - 1) * a6_spacing) / a4_n_per_row
        elif a7_block_first_position in ["start_from margin + spacing", "start_from margin + spacing(vertical centering)"]:
            w_block_size = (width_page_use - (a4_n_per_row + 1) * a6_spacing) / a4_n_per_row
        # ==========================================================

        w_block_size_int = int(w_block_size)
        h_block_size_int = w_block_size_int
        h_block_size = h_block_size_int
        w_block_size = w_block_size_int
        wh_per_block = f"{w_block_size_int}×{h_block_size_int}"

        n_per_col = height_page_use / h_block_size
        print(f"[✅] Column calc: height_use={height_page_use}, block_h={h_block_size} → {n_per_col:.4f}", end="")

        if int(n_per_col) == n_per_col:
            n_per_col_int = int(n_per_col)
        else:
            n_per_col_int = int(n_per_col) + 1

        # ========== ✅ 核心修复：垂直行高公式 - 完全适配 block_first_position ==========
        # 水平/垂直 公式完全对称，彻底修复 n_per_col_int -1 / +1 逻辑
        if a7_block_first_position == "start_from margin":
            h_guess = n_per_col_int * h_block_size + (n_per_col_int - 1) * a6_spacing
        elif a7_block_first_position in ["start_from margin + spacing", "start_from margin + spacing(vertical centering)"]:
            h_guess = n_per_col_int * h_block_size + (n_per_col_int + 1) * a6_spacing
        # ==========================================================================

        print(f" → init row={n_per_col_int} | h_guess={h_guess:.2f}")

        # ========== ✅ 同步修复：while循环内的行高重新计算公式 ==========
        while n_per_col_int > 1 and h_guess > height_page_use:
            n_per_col_int -= 1
            if a7_block_first_position == "start_from margin":
                h_guess = n_per_col_int * h_block_size + (n_per_col_int - 1) * a6_spacing
            elif a7_block_first_position in ["start_from margin + spacing",
                                          "start_from margin + spacing(vertical centering)"]:
                h_guess = n_per_col_int * h_block_size + (n_per_col_int + 1) * a6_spacing
            print(f"[✅] Reduce row to {n_per_col_int} → h_guess={h_guess:.2f}")
        # ==========================================================================

        blocks_per_page = a4_n_per_row * n_per_col_int
        page_count = 1 + (image_count_in_dir - 1) // blocks_per_page if image_count_in_dir > 0 else 0

        print(
            f"[✅] Final Params: {a4_n_per_row}×{n_per_col_int} blocks/page | Total pages: {page_count} | Block size: {wh_per_block}")

        all_concats = []
        # ========== 新增：判断是否开启纵向居中 ==========
        vertical_offset_mode = a7_block_first_position == "start_from margin + spacing(vertical centering)"
        # ==============================================
        for page in range(page_count):
            print(f"\n[✅] Processing Page {page + 1}/{page_count}")
            start_idx = page * blocks_per_page
            end_idx = min((page + 1) * blocks_per_page, image_count_in_dir)
            image_files_page = image_files[start_idx:end_idx]

            concat_page_np = self.create_single_concat_page(
                image_files_page, a2_width_page, height_page, a4_n_per_row,n_per_col_int,
                a5_margin, a6_spacing, a7_block_first_position,
                w_block_size, h_block_size, a8_draw_mode, a9_block_border, a10_block_border_style,
                a11_page_border, a12_page_border_style, page + 1,
                a13_save_blocks, blocks_final_path, a15_background_style,
                vertical_offset_mode, image_count_in_dir  # 传递纵向居中参数（第19个参数）
            )
            all_concats.append(concat_page_np)

        if all_concats:
            concat_np = np.stack(all_concats, axis=0)
        else:
            concat_np = np.zeros((1, 100, 100, 3), dtype=np.float32)
        concat_tensor = torch.from_numpy(concat_np)

        tips = self.get_node_tips()

        print(
            f"\n[✅] Generation Complete! | Tensor Shape: {concat_tensor.shape} | Alpha Channel: {concat_np.shape[-1] == 4}")
        if a13_save_blocks:
            print(f"[✅] Blocks saved to: {blocks_final_path}")
        print("=" * 60)

        return (concat_tensor, page_count, wh_per_block, image_count_in_dir, blocks_final_path, tips)


# Register node
NODE_CLASS_MAPPINGS["ImageConcatNode"] = ImageConcatNode
NODE_DISPLAY_NAME_MAPPINGS["ImageConcatNode"] = "Image concatenate(QQ2540968810)"

if __name__ == "__main__":
    print("✅ Png Alpha Channel + Block Start Position Node Registered Successfully!")