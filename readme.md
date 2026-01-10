<font face="微软雅黑" size="4" color="#f0f000">Comfyui-Image-Concat - a powerful image concatenation tool</font>

✨ Core Features (Latest Update: Auto Horizontal Centering + Optional Vertical Centering)

This node is a powerful image concatenation tool for ComfyUI, with True Alpha Channel Support and Multiple Image-block Fill Modes:
<div style="font-size: 20px;"><b>I. Key Capabilities</b></div>

1.  **Multiple Image-block Fill Modes** (Image resizing mode for each block)

   - 1.smaller value filler: Fill the block with the smaller value of the origin image's long side and the block's width (maintains aspect ratio)
   - 2.Stretches image to fill: Stretches image to fill block (may distort aspect ratio)
   - 3.zoom Long side(recommend): zoom long side of origin image to block width (maintains aspect ratio), then fill the block
   - 4.crop square by short side: Crops square by short side of origin image(maintains aspect ratio), then zoom it to fill the block fully

2. Flexible Block Start Position Control:

- start_from margin: Blocks start directly at page margin (top/left aligned)
- start_from margin + spacing: Blocks start with extra spacing (top aligned)
- start_from margin + spacing(vertical centering): Auto vertical centering + horizontal centering

3. Optional Vertical Centering: Enabled via start_from margin + spacing(vertical centering) option

4. Multiple Background Styles: Light (white) / Dark (black) / Transparent (alpha channel)

5. Custom Border Styles:
Block/Page borders: Rectangle / Rounded (10/20/30 radius)
Border line styles: Solid / Dashed / Dotted / Dash-dot (fixed dashed line rendering bugs)

6. True 4-Channel Alpha Transparency: Export PNGs with full RGBA support (transparent background for margins/spacing/empty areas)
![background_style][def1]

7. Save Individual Blocks: Export each image block as separate PNG (with alpha channel)

<div style="font-size: 20px;"><b>II. Input Parameters</b></div>

![input_parameter][def2]

<div style="font-size: 20px;"><b>III. 📤 Outputs</b></div>

![output_parameter][def3]

<div style="font-size: 20px;"><b>IV. Usage Examples </b></div>

✅1. Basic usage

   - (1) In the ComfyUI page, double-click mouse to search for "concat", locate the `Image Concatenate(QQ2540968810)` node, and click it to insert it into the ComfyUI page, or drag the following image into the  ComfyUI page ;

   ![image_concat3][def4]

  Note: the above image can be found in "custom_nodes\Comfyui-Image-Concat\images\image_concat3.png".

   - (2) Input directory path of images into `a1_image_dir` ;  
   - (3) Connect `b1_concat_images` output port to `image preview` node or  `image save` node;  
   - (4) Input other parameters or Switch dropdown box if necessary;
   - (5) Run to the `Image Concatenate(QQ2540968810)` node to get concated image(s) in `comfyui/out` directory;

   Note: You can get help information about this node by connecting output `b6_tips` port to `preview any` node.

✅2. other workflow example (list by `a8_draw_mode`)

- (1)  small value filler

 Set your input port as below, you'll see 4 (show by `b2_page_count` out port) concated images.
If you set `a13_save_blocks` = true, you can get all block files which you see in concated images in 'comfyui/concat_blocks' directory(you can modify it by `a14_blocks_save_dir` input port).

![image_concat1][def5]

  Note: the above image can be found in "custom_nodes\Comfyui-Image-Concat\images\image_concat1.png". You can drag the it into the  ComfyUI page to run this example workflow.

- (2)  stretches image to fill

Set your input port as below, you'll get 1 (show by `b2_page_count` out port) concated picture file in 'comfyui/output' directory.
If you set `a15_background_style` = "transparent(alpha channel)", you can get picture file with RGBA channel. So you can edit its background layer in PS.
If you set `a13_save_blocks` = "true", you can get all block files which you see in concated picture in 'comfyui/concat_blocks' directory(you can modify it by `a14_blocks_save_dir` input port).

![image_concat1][def6]

  Note: the above image can be found in "custom_nodes\Comfyui-Image-Concat\images\image_concat2.png". You can drag the it into the  ComfyUI page to run this example workflow.

- (3)  crop square by short side

Set your input port as below, you'll get 2 (show by `b2_page_count` out port) concated picture files in 'comfyui/output' directory.
You can adjust `a3_aspect_ratio` input port to get vertical concated image picture.
If you want the spliced graphic blocks to be centered vertically, you should set `a7_block_first_position` = "start_from margin + spacing(vertical centering)".
If you set `a15_background_style` = "transparent(alpha channel)", you can get picture file with RGBA channel. So you can edit its background layer in PS.

![image_concat1][def7]

  Note: the above image can be found in "custom_nodes\Comfyui-Image-Concat\images\image_concat4.png". You can drag the it into the  ComfyUI page to run this example workflow.
  Clicking https://drive.google.com/file/d/1in6XwuYF-DbZA8zPcgrFiY4NU4y-r_zp/view?usp=drive_link or click https://pan.baidu.com/s/1fu2_7Z3oOLG_LrHBd1Mk0w?pwd=gpan to download our source image zip file. Unzip it to any folder, you will get 59 source image files.


<div style="font-size: 20px;"><b>V. Installation method </b></div>

1. Manual Installation (Recommended) 

   (1) cd Comfy\custom_nodes;

   (2) git clone https://github.com/shmbatom/Comfyui-Image-Concat.git ;

   (3) Restart the ComfyUI Service.

2. Installation via Manager 

   (1) Search  for "Comfyui-Image-Concat" in the ComfyUI Manager and install 
it into ComfyUI/custom_nodes directory;

   (2) Restart ComfyUI;

   (3) Find the node under `Image Processing/concat→Image concatenate(QQ2540968810)`.

<div style="font-size: 20px;"><b>VI. Notes</b></div>

1. All output images maintain alpha channel (PNG format recommended)
2. Saved block images include borders and alpha channel
3. Border color auto-adapts to background style (white on dark, black on light/transparent)
4. block group centering:
- Horizontal Centering: Automatically calculates X offset 
- Vertical Centering (Optional)
Only enabled when you set `a7_block_first_position` = "start_from margin + spacing(vertical centering)".
5. Maximum page size: 50000px (adjust max in INT parameters if needed)
6. Supported image formats: PNG, JPG, JPEG, BMP, GIF

<div style="font-size: 20px;"><b>VII. 💡 Tips </b></div>

1. For best results with transparent background: Use PNG format for input images
2. Zoom Long side (recommend) resize mode preserves image aspect ratio
3. Rounded borders with radius 20 work best for block sizes > 500px
4. Enable "Save individual block images" for post-processing single blocks

<div style="font-size: 20px;"><b>VIII. Donation</b></div>

If you think this tool is decent, you can donate a cup of coffee to me.

![donate_me][def9]

[def1]: images/backgroud.png
[def2]: images/parameter.png
[def3]: images/out.png
[def4]: images/image_concat3.png
[def5]: images/image_concat1.png
[def6]: images/image_concat2.png
[def7]: images/image_concat4.png
[def9]: images/donate.png
