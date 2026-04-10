import os
import base64
from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
import config.config as config

class SentenceTransformerEmbeddings:
    """SentenceTransformer 包装类，兼容 Chroma embedding_function 接口"""
    def __init__(self, model_path):
        self.model = SentenceTransformer(model_path)

    def embed_documents(self, texts):
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text):
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()

def get_bge_embedding_model():
    """配置 BAAI/bge-small-zh-v1.5 本地词嵌入模型"""
    local_cache = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "model_cache_full")
    return SentenceTransformerEmbeddings(local_cache)

def get_glm4_llm():
    """配置GLM-4-Flash 模型"""
    return ChatOpenAI(
        model="glm-4-flash",  
        temperature=config.TEMPERATURE,
        openai_api_base=config.GLM_API_BASE,
        openai_api_key=os.environ["GLM_API_KEY"],
        max_tokens=config.MAX_TOKENS
    )

def image_to_base64(image_path: str) -> str:
    """将图片文件转换为 Base64 字符串"""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"未找到图片文件: {image_path}")
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
