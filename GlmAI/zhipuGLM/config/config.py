# config.py

import os
from dotenv import load_dotenv

# 加载 .env 文件
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(dotenv_path=dotenv_path)

# ==========================
# API 配置
# =========================================================

# GLM-4.1V-Thinking-Flash 配置
GLM_API_BASE = "https://open.bigmodel.cn/api/paas/v4/"

# --- 词嵌入模型配置 ---
BGE_EMBEDDING_MODEL_NAME = "BAAI/bge-small-zh-v1.5"

# ==========================
# 路径配置
# ==========================

# 获取 zhipuGLM 模块的根目录
_MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 存放 TXT 病历文件的文件夹
DOCS_DIRECTORY = os.path.join(_MODULE_DIR, "medical_docs")

# 向量数据库存储路径
CHROMA_PERSIST_DIR = os.path.join(_MODULE_DIR, "chroma_db_medical")

# 默认测试图片路径
DEFAULT_IMAGE_PATH = os.path.join(_MODULE_DIR, "pic", "tongue_sample.png")

# LLM 参数
MAX_TOKENS = int(os.getenv("GLM_MAX_TOKENS", "512"))
TEMPERATURE = 0.0

# 模型名称配置（通过环境变量可覆盖，方便模型升级时切换）
AI_PRIMARY_MODEL = os.getenv("AI_PRIMARY_MODEL", "glm-4.5-air")   # 首选模型
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "glm-4-flash") # 降级模型
AI_VISION_MODEL = os.getenv("AI_VISION_MODEL", "glm-4v-flash")   # 视觉模型
AI_SUPPLEMENT_MODEL = os.getenv("AI_SUPPLEMENT_MODEL", "glm-4.5-air")  # RAG补充模型
AI_REPORT_MODEL = os.getenv("AI_REPORT_MODEL", "glm-4.5-air")          # 病历生成模型
