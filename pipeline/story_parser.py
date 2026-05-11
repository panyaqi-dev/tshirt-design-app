"""
故事拆解模块
对应任务书 §3.1：从故事中识别核心意象、延展场景、符号性元素
对应任务书 §3.3：根据各版位的设计逻辑生成差异化 prompt

核心策略：
- 输入故事 + 从参考图提取的风格描述
- LLM 输出 4 个版位的英文 prompt，每个都嵌入相同的风格描述
- 这样 4 个 prompt 在文本层面就强制共享了视觉风格锚点
"""
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv(override=True)

# 通义千问通过 OpenAI 兼容模式调用
client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv(
        "LLM_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ),
)
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-plus")


SYSTEM_PROMPT = """你是一位资深 T 恤设计师 + AI 绘画 prompt 工程师。

【任务】
根据用户提供的"故事文本"和"风格描述"，为一件 T 恤的 4 个版位分别生成英文图像生成 prompt。

【4 个版位的设计逻辑】

1. front_chest（前胸主图，约 25×25 cm）：
   - 主视觉，承载故事最核心的意象
   - 信息量最大、构图饱满、视觉冲击强

2. back（后背图，约 30×35 cm）：
   - 叙事性表达
   - 包含延展场景、人物动作、或多元素组合
   - 信息量中高

3. sleeve（袖口图，约 5×8 cm）：
   - 极简符号化
   - 单一图标或一个超短词
   - 信息密度极低（5cm 范围内必须能看清）

4. badge（胸章图，约 8×8 cm）：
   - 章印感、徽章感
   - 浓缩符号 + 短词组合
   - 类似传统印章或品牌徽标

【两个核心要求】

A. **风格一致性**（最重要！）：
   每个 prompt 都必须在末尾包含完全相同的风格描述（用户给的 style description 原文照搬）
   不能改写、不能简化、不能拆分

B. **内容差异化**：
   4 个 prompt 的画面内容主题必须有明显差异，呼应各版位的设计逻辑

【输出格式】
只输出一个 JSON 对象，不要任何其他文字。结构如下：

{
  "style_anchor": "（中文简述）这套设计的统一关键词，例如：东方水墨 + 黛青留白 + 极简笔意",
  "front_chest": "完整英文 prompt",
  "back": "完整英文 prompt",
  "sleeve": "完整英文 prompt",
  "badge": "完整英文 prompt"
}

每个英文 prompt 的结构：
"[内容描述：呼应该版位的设计逻辑], [视觉细节], [统一的 style description], isolated on white background, t-shirt design, high quality"
"""


def decompose_story(story_text: str, style_description: str) -> dict:
    """
    将故事 + 风格描述 → 4 个版位的 prompt

    Args:
        story_text: 用户输入的故事文本
        style_description: 来自风格提取模块的英文风格描述

    Returns:
        dict: {style_anchor, front_chest, back, sleeve, badge}
    """
    user_msg = f"""【故事文本】
{story_text}

【风格描述】（必须在每个 prompt 中原文嵌入）
{style_description}

请按系统指令的格式输出 JSON。"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.7,
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    # 校验必需字段
    required = ["style_anchor", "front_chest", "back", "sleeve", "badge"]
    for key in required:
        if key not in result:
            raise ValueError(f"LLM 输出缺少字段: {key}")

    return result


if __name__ == "__main__":
    # 本地测试（只需 DASHSCOPE_API_KEY）
    test_story = """
    "吾所以有大患，为吾有身"，"有身"指的是过度执着于"我"。
    爸爸去接哥哥放学，哥哥因为害羞不敢一起走——其实同学根本不会在意，是哥哥自己想象出来的。
    放下"小我"，与万物融为一体，烦恼自然就少了。
    """
    test_style = (
        "Traditional Chinese ink wash painting style, monochromatic black-and-grey palette "
        "with subtle ink gradients, expressive brushstrokes, minimalist composition with "
        "abundant white space, sumi-e aesthetic, calligraphic linework, contemplative mood, "
        "loose and flowing texture, oriental art language."
    )

    result = decompose_story(test_story, test_style)
    print(json.dumps(result, ensure_ascii=False, indent=2))
