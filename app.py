"""
故事生成 T 恤设计 Web 应用
主程序：Gradio Web UI + 完整生成管线

完整流程：
  参考图 → 风格提取（Qwen-VL）
       ↓
  故事 + 风格描述 → 故事拆解（qwen-turbo）→ 4 个版位 prompt
       ↓
  每个 prompt → 图像生成（通义万相）→ 4 张设计图
       ↓
  4 张设计图 → Mockup 合成（Pillow）→ 正面/背面效果图
"""
import os
import io
import zipfile
import gradio as gr
from PIL import Image
from dotenv import load_dotenv

from pipeline.style_extractor import extract_style
from pipeline.story_parser import decompose_story
from pipeline.image_generator import generate_design_image
from pipeline.mockup_composer import compose_mockup

load_dotenv(override=True)

POSITION_NAMES = {
    "front_chest": "前胸主图",
    "back": "后背图",
    "sleeve": "袖口图",
    "badge": "胸章图",
}


def generate_designs(story_text, reference_image, progress=gr.Progress()):
    """完整生成管线"""

    if not story_text or len(story_text.strip()) < 50:
        raise gr.Error("故事文本至少 50 字")
    if reference_image is None:
        raise gr.Error("请上传一张风格参考图")

    # Step 1: 风格提取
    progress(0.05, desc="🎨 分析参考图风格中...")
    style_description = extract_style(reference_image)
    print("=" * 60)
    print("【风格描述】")
    print(style_description)

    # Step 2: 故事拆解
    progress(0.20, desc="📖 拆解故事到 4 个版位...")
    prompts = decompose_story(story_text, style_description)
    print("=" * 60)
    print(f"【风格锚点】{prompts.get('style_anchor', '')}")
    for pos in ["front_chest", "back", "sleeve", "badge"]:
        print(f"\n[{POSITION_NAMES[pos]}] {prompts[pos][:120]}...")

    # Step 3: 4 个版位逐个生成（共享同一种子）
    designs = {}
    positions = ["front_chest", "back", "sleeve", "badge"]
    for i, pos in enumerate(positions):
        progress(0.30 + 0.55 * (i / 4), desc=f"🖼️ 生成{POSITION_NAMES[pos]}...")
        designs[pos] = generate_design_image(
            prompt=prompts[pos],
            position=pos,
            seed=42,  # 固定种子，所有图共用
        )

    # Step 4: Mockup 合成
    progress(0.90, desc="👕 合成 T 恤效果图...")
    mockup_front = compose_mockup(designs, side="front")
    mockup_back = compose_mockup(designs, side="back")

    progress(1.0, desc="✅ 完成")

    return (
        designs["front_chest"],
        designs["back"],
        designs["sleeve"],
        designs["badge"],
        mockup_front,
        mockup_back,
    )


def package_zip(front, back, sleeve, badge, mockup_f, mockup_b):
    """打包为 zip"""
    import numpy as np

    images = [front, back, sleeve, badge, mockup_f, mockup_b]
    names = [
        "01_前胸主图.png",
        "02_后背图.png",
        "03_袖口图.png",
        "04_胸章图.png",
        "05_T恤正面.png",
        "06_T恤背面.png",
    ]
    os.makedirs("outputs", exist_ok=True)
    output_path = "outputs/tshirt_designs.zip"
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for img, name in zip(images, names):
            if img is None:
                continue
            # 兼容多种输入类型:PIL.Image / numpy 数组 / 文件路径字符串
            if isinstance(img, str):
                img = Image.open(img)
            elif isinstance(img, np.ndarray):
                img = Image.fromarray(img)
            buf = io.BytesIO()
            if img.mode == "RGBA":
                img = img.convert("RGB")  # PNG 也能存 RGBA,但保险起见统一转
                img.save(buf, format="PNG")
            else:
                img.save(buf, format="PNG")
            zf.writestr(name, buf.getvalue())
    return output_path


with gr.Blocks(title="故事生成 T 恤设计", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎨 故事生成 T 恤设计 Web 应用")
    gr.Markdown(
        "输入一段故事 + 一张风格参考图，自动生成一套 4 版位 T 恤设计 + 上身效果图\n\n"
        "**技术栈**：阿里云百炼（Qwen-VL 风格提取 + Qwen-Plus 故事拆解 + 通义万相图像生成）"
    )

    with gr.Row():
        with gr.Column(scale=1):
            story_input = gr.Textbox(
                label="📖 故事文本（50-500 字）",
                lines=10,
                placeholder="可输入诗词、神话、生活叙事等...",
            )
            reference_input = gr.Image(label="🖼️ 风格参考图", type="pil", height=300)
            generate_btn = gr.Button("🚀 生成设计", variant="primary", size="lg")

        with gr.Column(scale=2):
            gr.Markdown("### 四个版位设计")
            with gr.Row():
                front_chest_out = gr.Image(label="前胸主图 (25×25cm)", height=250)
                back_out = gr.Image(label="后背图 (30×35cm)", height=250)
            with gr.Row():
                sleeve_out = gr.Image(label="袖口图 (5×8cm)", height=250)
                badge_out = gr.Image(label="胸章图 (8×8cm)", height=250)

            gr.Markdown("### T 恤效果图")
            with gr.Row():
                mockup_front_out = gr.Image(label="正面", height=300)
                mockup_back_out = gr.Image(label="背面", height=300)

            with gr.Row():
                zip_btn = gr.Button("📦 打包下载所有图", variant="secondary")
                zip_output = gr.File(label="下载")

    generate_btn.click(
        fn=generate_designs,
        inputs=[story_input, reference_input],
        outputs=[
            front_chest_out, back_out, sleeve_out, badge_out,
            mockup_front_out, mockup_back_out,
        ],
    )

    zip_btn.click(
        fn=package_zip,
        inputs=[
            front_chest_out, back_out, sleeve_out, badge_out,
            mockup_front_out, mockup_back_out,
        ],
        outputs=zip_output,
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
