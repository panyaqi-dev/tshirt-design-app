"""
图像生成模块
对应任务书 §3.2 风格一致性 + §3.3 版位差异化

策略：
- 使用阿里云通义万相文生图（wanx2.1-t2i-turbo）
- 4 张图共享同一种子（seed），增强一致性
- 4 张图的 prompt 都嵌入了相同的 style description（来自风格提取）
- 4 张图独立的 size 参数体现版位差异化
"""
import os
import io
import time
import requests
import dashscope
from dotenv import load_dotenv
load_dotenv(override=True)
from dashscope import ImageSynthesis
from PIL import Image

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "wanx2.1-t2i-turbo")

# 各版位的输出尺寸
# 注意：wanx2.1-t2i-turbo 支持的常见尺寸为 1024*1024, 720*1280, 1280*720, 等
# 这里统一用 1024*1024 简化（mockup 阶段会按版位再做缩放裁剪）
POSITION_SIZES = {
    "front_chest": "1024*1024",   # 1:1 主视觉
    "back": "720*1280",            # 9:16 后背（接近 4:5）
    "sleeve": "1024*1024",         # 1:1，小版位 mockup 时再裁
    "badge": "1024*1024",          # 1:1 章印
}


def generate_design_image(
    prompt: str,
    position: str,
    seed: int = 42,
    reference_image=None,  # 暂时未用，预留接口
) -> Image.Image:
    """
    生成单张设计图

    Args:
        prompt: 完整的英文 prompt（已包含风格描述）
        position: "front_chest" / "back" / "sleeve" / "badge"
        seed: 随机种子，固定为 42 以增强一致性
        reference_image: 预留参数（当前版本通过 prompt 中的风格描述实现一致性）

    Returns:
        PIL.Image: 生成的设计图
    """
    size = POSITION_SIZES[position]

    rsp = ImageSynthesis.call(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        model=IMAGE_MODEL,
        prompt=prompt,
        n=1,
        size=size,
        seed=seed,
    )

    if rsp.status_code != 200:
        raise RuntimeError(
            f"图像生成失败 [{position}]: status={rsp.status_code}, "
            f"code={rsp.code}, message={rsp.message}"
        )

    if not rsp.output or not rsp.output.results:
        raise RuntimeError(f"图像生成成功但没有返回结果 [{position}]")

    image_url = rsp.output.results[0].url

    # 下载图片
    for attempt in range(3):
        try:
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
        except Exception as e:
            if attempt == 2:
                raise
            print(f"下载重试 {attempt + 1}/3: {e}")
            time.sleep(2)


if __name__ == "__main__":
    # 本地测试（只需 DASHSCOPE_API_KEY）
    test_prompt = (
        "A minimalist ink painting of a single lotus root cross-section showing its "
        "hollow chambers, traditional Chinese ink wash style, monochromatic black-and-grey, "
        "expressive brushstrokes, abundant white space, isolated on white background, "
        "t-shirt design, high quality"
    )
    img = generate_design_image(prompt=test_prompt, position="badge", seed=42)
    img.save("test_output.png")
    print(f"✓ 生成成功，保存到 test_output.png ({img.size})")
