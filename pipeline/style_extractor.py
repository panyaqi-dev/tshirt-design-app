"""
风格提取模块
对应任务书 §3.2 一致性控制的核心环节

策略：用 Qwen-VL 视觉语言模型分析参考图，提取出可文字化的风格描述
这个风格描述会注入到 4 个版位的 prompt 中，作为风格一致性的"文字锚点"
"""
import os
import io
import base64
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)
from PIL import Image

# Qwen-VL 通过 OpenAI 兼容模式调用
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)
VLM_MODEL = os.getenv("VLM_MODEL", "qwen-vl-plus")


STYLE_PROMPT = """请仔细分析这张参考图的【纯视觉风格特征】，从以下 4 个维度概括：

1. **色彩体系**：主色调、辅助色、冷暖倾向、饱和度高低
2. **笔触/质感**：如水墨、扁平矢量、像素、油画、版画、3D 渲染等
3. **构图气质**：极简留白 / 繁复堆叠 / 对称 / 不对称 / 动态 / 静态
4. **艺术语言**：流派归属，如东方水墨、波普艺术、复古版画、赛博朋克、新中式等

输出要求：
- 用 100-180 字英文输出（用于后续图像生成 prompt）
- 只描述风格本身，不要描述图中的具体物体或主题
- 用形容词和风格关键词为主，避免完整句子
- 风格描述要可被其他图像生成模型理解并复现

直接输出英文风格描述，不要任何其他文字（不要"Sure"、"Here is"等开场白）。"""


def image_to_base64(image: Image.Image) -> str:
    """PIL Image → base64 字符串"""
    buf = io.BytesIO()
    if image.mode != "RGB":
        image = image.convert("RGB")
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def extract_style(reference_image: Image.Image) -> str:
    """
    从参考图中提取风格描述
    返回一段英文描述，用于作为 4 个版位 prompt 的风格锚点
    """
    img_b64 = image_to_base64(reference_image)
    image_data_url = f"data:image/png;base64,{img_b64}"

    response = client.chat.completions.create(
        model=VLM_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                    {"type": "text", "text": STYLE_PROMPT},
                ],
            }
        ],
        temperature=0.3,  # 低温度，保证风格描述的稳定性
    )

    style_description = response.choices[0].message.content.strip()
    return style_description


if __name__ == "__main__":
    # 本地测试
    test_image = Image.new("RGB", (512, 512), (200, 100, 50))
    style = extract_style(test_image)
    print("提取到的风格描述：")
    print(style)
