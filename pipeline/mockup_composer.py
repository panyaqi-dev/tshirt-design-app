"""
Mockup 合成模块
对应任务书 §3.4：将设计图合成到 T 恤模板

策略：
- Pillow 贴图
- 设计图白色背景透明化（处理融合问题）
- 各版位独立的位置 + 尺寸映射
"""
import os
from PIL import Image, ImageDraw

TEMPLATE_DIR = "assets"

# 假设 T 恤模板尺寸为 1200×1500 像素
# 实际使用时根据所选模板调整以下坐标
POSITION_LAYOUT_FRONT = {
    "front_chest": {"position": (450, 420), "size": (300, 300)},
    "badge": {"position": (820, 380), "size": (90, 90)},
    "sleeve": {"position": (1075, 480), "size": (60, 100)},
}

POSITION_LAYOUT_BACK = {
    "back": {"position": (400, 380), "size": (400, 500)},
}


def remove_white_bg(image: Image.Image, threshold: int = 240) -> Image.Image:
    """简单移除白色背景，让设计图融入 T 恤底色"""
    image = image.convert("RGBA")
    pixels = image.load()
    width, height = image.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if r > threshold and g > threshold and b > threshold:
                pixels[x, y] = (r, g, b, 0)
    return image


def create_placeholder_tshirt(side: str = "front") -> Image.Image:
    """没有 T 恤模板图时，自动生成一个简化的 T 恤轮廓占位"""
    img = Image.new("RGBA", (1200, 1500), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 简化 T 恤轮廓
    tshirt_shape = [
        (300, 200),
        (100, 350),
        (200, 600),
        (300, 500),
        (300, 1300),
        (900, 1300),
        (900, 500),
        (1000, 600),
        (1100, 350),
        (900, 200),
        (750, 250),
        (600, 280),
        (450, 250),
    ]
    draw.polygon(
        tshirt_shape,
        fill=(245, 245, 245, 255),
        outline=(180, 180, 180, 255),
    )

    # 标注一下是正面还是背面
    label = "FRONT" if side == "front" else "BACK"
    draw.text((550, 1350), label, fill=(180, 180, 180, 255))

    return img


def compose_mockup(designs: dict, side: str = "front") -> Image.Image:
    """
    把设计图合成到 T 恤模板上

    designs: {"front_chest": Image, "back": Image, "sleeve": Image, "badge": Image}
    side: "front" / "back"
    """
    template_path = os.path.join(TEMPLATE_DIR, f"tshirt_{side}.png")

    if os.path.exists(template_path):
        template = Image.open(template_path).convert("RGBA")
    else:
        template = create_placeholder_tshirt(side)

    layout = POSITION_LAYOUT_FRONT if side == "front" else POSITION_LAYOUT_BACK

    for pos_name, layout_info in layout.items():
        if pos_name not in designs or designs[pos_name] is None:
            continue

        design = designs[pos_name].convert("RGBA")
        design = design.resize(layout_info["size"], Image.LANCZOS)
        design = remove_white_bg(design)

        template.paste(design, layout_info["position"], design)

    return template


if __name__ == "__main__":
    # 本地测试：创建占位图
    img = create_placeholder_tshirt("front")
    img.save("test_tshirt_front.png")
    print("Saved test_tshirt_front.png")
