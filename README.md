# 🎨 故事生成 T 恤设计 Web 应用

> 输入一段故事 + 一张参考图，自动生成一套**四版位**风格统一的 T 恤设计 + 上身 mockup。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)]()
[![Gradio](https://img.shields.io/badge/Gradio-4.x-orange.svg)]()
[![阿里云百炼](https://img.shields.io/badge/Powered_by-阿里云百炼-FF6A00.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

---

## ✨ 项目特色

- 🧠 **智能拆解**：LLM 自动将故事转化为 4 个版位的差异化视觉 prompt——前胸主图饱满、后背图叙事、袖口极简、胸章章印感
- 🎯 **三重一致性保障**：文本风格锚点 + 固定随机种子 + 统一 Prompt 模板，让 4 张图风格高度统一
- 🇨🇳 **中文场景优化**：基于阿里云百炼（Qwen-VL + Qwen-Turbo + 通义万相），对传统文化叙事理解深刻
- 💰 **零成本可跑**：使用免费 API 额度即可完成全部调试与三套作品产出
- 🚀 **极简部署**：单一 API Key + 一行命令启动，无需本地 GPU

---

## 🚀 快速开始

### 前置要求

- **Python 3.10+**（推荐 3.11；3.7 等老版本**不支持** Gradio 4.x）
- **阿里云账号**（[bailian.console.aliyun.com](https://bailian.console.aliyun.com)，需实名认证）
- 一个 API Key（一个 key 通用所有模型）

### 三步运行

```bash
# 1. 克隆 / 解压项目，进入目录
cd tshirt-design-app

# 2. 创建虚拟环境并安装依赖
python -m venv venv
.\venv\Scripts\Activate.ps1          # Windows
# source venv/bin/activate           # macOS / Linux
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env，把 DASHSCOPE_API_KEY 改成你自己的 key

# 4. 启动！
python app.py
```

浏览器打开 **http://localhost:7860**，输入故事 + 参考图，点击"🚀 生成设计"。

> 💡 **首次运行**：30 秒生成 4 张设计图 + 2 张 mockup，单次调用约消耗 ¥0.05–0.1（首月免费额度内可跑约 50 次）。

---

## 🏗️ 系统架构

```
   参考图 ──┐
            ├─→  Qwen-VL 风格提取  ──→  英文风格描述（Style Anchor）
            ↓
   故事 + 风格描述 ──→  Qwen-Turbo 拆解  ──→  4 个版位 Prompt（共享 Style Anchor）
                                              ↓
                                    通义万相 × 4（同一种子）
                                              ↓
                                  4 张设计图  ──→  Pillow 合成
                                                   ↓
                                              T 恤正面 + 背面 mockup
```

**5 个解耦模块**，每个都可单独测试。

---

## 📁 项目结构

```
tshirt-design-app/
├── app.py                          # Gradio Web UI + 完整管线编排
├── pipeline/
│   ├── __init__.py
│   ├── style_extractor.py          # 参考图 → 英文风格描述（Qwen-VL）
│   ├── story_parser.py             # 故事 + 风格 → 4 个版位 prompt（Qwen-Turbo）
│   ├── image_generator.py          # prompt → 设计图（通义万相）
│   └── mockup_composer.py          # 设计图 → T 恤效果图（Pillow）
├── assets/                         # T 恤模板（可选；缺失时自动生成占位）
├── outputs/                        # 生成结果
│   ├── 作品01_反者道之动/
│   ├── 作品02_人能弘道/
│   └── 作品03_无身/
├── requirements.txt
├── .env.example                    # API Key 配置模板
└── README.md
```

---

## 🎨 三套示范作品

| 编号 | 命题 | 故事核心 | 视觉适配度 |
|------|------|---------|----------|
| 作品 01 | 自选 1（《反者道之动》） | 贪小便宜的代价（藕 + 九宫洛书） | 高 |
| 作品 02 | 自选 2（《人能弘道》） | AI 时代的"道"与"术" | 中高 |
| 作品 03 | 命题 A（道德经·无身） | 放下小我，与万物融合 | 中 |

> 三套作品共用同一张齐白石虫鱼水墨参考图，验证了系统在不同抽象程度故事上的稳定性与跨作品风格一致性。

---

## 🔍 核心技术亮点

### 风格一致性的三重保障策略 ★

| 层级 | 机制 | 作用 |
|------|------|------|
| ① 文本锚点 | Qwen-VL 输出的英文风格描述被原文嵌入到 4 个 prompt 中 | 文字层面统一指令 |
| ② 种子固定 | 4 张图共用 `seed = 42` | 在扩散模型的随机性上加确定性约束 |
| ③ 模板统一 | 4 个 prompt 共享相同的开头/结尾结构 | 保持模型注意力分布一致 |

理论依据：扩散模型在「同一 seed + 同一风格描述 + 不同主体」条件下，会保留高度一致的视觉风格。

### 单独调试每个模块

```bash
python -m pipeline.style_extractor    # 测试风格提取
python -m pipeline.story_parser       # 测试故事拆解
python -m pipeline.image_generator    # 测试图像生成（消耗 1 张额度）
```

---

## 🐛 常见问题排查

实际开发中遇到并解决的真实问题，记录在此供参考：

### Q1: 报错 `openai.AuthenticationError: invalid_api_key`，但 `.env` 里 key 明明是对的

**原因**：`load_dotenv()` 默认不覆盖系统已存在的环境变量。如果系统中有同名变量，`.env` 里的值会被忽略。

**解决**：本项目在每个模块顶部都使用 `load_dotenv(override=True)` 强制覆盖。

如仍有问题，验证 key 实际加载值：

```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(override=True); print(os.getenv('DASHSCOPE_API_KEY')[:10])"
```

### Q2: `pip install` 报错 `Requires-Python >=3.8`

**原因**：使用了过老的 Python 创建 venv。venv 一旦创建，Python 版本就固定了，**装新 Python 不会自动升级现有 venv**。

**解决**：销毁旧 venv，用启动器显式指定新版本：

```powershell
Remove-Item -Recurse -Force venv         # Windows
# rm -rf venv                            # macOS / Linux

py -3.11 -m venv venv                    # Windows 显式指定 3.11
# python3.11 -m venv venv                # macOS / Linux
```

### Q3: 打包下载报错 `'numpy.ndarray' object has no attribute 'save'`

**原因**：Gradio 4.x 在前后端传递图像时会自动将 PIL Image 转为 numpy 数组。

**解决**：本项目的 `package_zip` 已加入类型判断（PIL Image / numpy / 文件路径都兼容）。

### Q4: pip 报 `ProxyError: Cannot connect to proxy`

**原因**：环境变量中残留了代理设置，但代理软件未启动。

**解决**：

```powershell
$env:HTTP_PROXY=""; $env:HTTPS_PROXY=""; $env:http_proxy=""; $env:https_proxy=""
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## ⚠️ 已知局限

本项目作为限时框架版本（开发投入约 4 小时），有意识地做了以下取舍：

- **一致性方法仅用 1 种**（纯文本 + 固定种子），未对比 IP-Adapter / ControlNet
- **Mockup 模板**使用程序生成的占位 T 恤，未叠加真实材质
- **白底去除**使用阈值法，对复杂背景效果有限
- **未做 prompt 失败重试机制**，个别失败 case 需手动调整

详细的局限分析与改进方向，请见技术报告 §8。

---

## 📚 进一步阅读

- 📄 [**技术报告（完整版）**](./技术报告_故事生成T恤设计.docx) — 11 页技术报告，含选型对比、方法论、实验数据、踩坑沉淀
- 🌐 [阿里云百炼控制台](https://bailian.console.aliyun.com)
- 🤗 [Gradio 官方文档](https://www.gradio.app/docs/)

---

## 🧰 技术栈

| 组件 | 选用 | 备选方案 |
|------|------|---------|
| 大语言模型 | qwen-turbo | qwen-plus / deepseek-v3 / qwen3-flash |
| 视觉语言模型 | qwen-vl-plus | qwen-vl-max |
| 图像生成 | wanx2.1-t2i-turbo | wan2.6-t2i / wanx2.1-t2i-plus |
| Web 框架 | Gradio 4.x | Streamlit / FastAPI |
| 图像处理 | Pillow | OpenCV |
| 配置管理 | python-dotenv | hydra |

---

## 📝 License

MIT — 自由使用，标注来源即可。

---

> 💬 一个故事 → 一件衣服。AI 让叙事变成穿戴的视觉语言。
