import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
import config.config as config
import utils.utils as utils

def build_or_load_rag_index(docs_dir: str = None, persist_dir: str = None):
    """加载或从文档构建向量数据库
    
    Args:
        docs_dir: 文档目录，默认使用配置中的 DOCS_DIRECTORY 或 post_surgery_care 目录
        persist_dir: 持久化目录，默认使用配置中的 CHROMA_PERSIST_DIR
    """
    print(f"--- [DEBUG] 开始加载 BGE 嵌入模型 ---")
    bge_embeddings = utils.get_bge_embedding_model()
    print(f"--- [DEBUG] BGE 嵌入模型加载完成 ---")

    persist_dir = persist_dir or config.CHROMA_PERSIST_DIR
    print(f"--- [DEBUG] persist_dir: {persist_dir} ---")

    if os.path.exists(persist_dir):
        print(f"--- 正在加载现有 Chroma 数据库: {persist_dir} ---")
        print(f"--- [DEBUG] 开始加载 Chroma ---")
        try:
            import chromadb
            print(f"--- [DEBUG] 创建 Chroma 客户端 ---")
            chroma_client = chromadb.PersistentClient(path=persist_dir)
            print(f"--- [DEBUG] Chroma 客户端创建成功，开始加载集合 ---")
            result = Chroma(client=chroma_client, embedding_function=bge_embeddings)
            print(f"--- [DEBUG] Chroma 加载完成 ---")
            return result
        except Exception as e:
            print(f"--- [ERROR] Chroma 加载失败: {e} ---")
            import traceback
            traceback.print_exc()
            return None

    docs_dir = docs_dir or config.DOCS_DIRECTORY
    if not os.path.exists(docs_dir):
        print(f"--- 错误：请创建 {docs_dir} 文件夹 ---")
        return None

    print(f"--- 正在加载文档并构建向量数据库: {docs_dir} ---")
    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, length_function=len)
    chunks = text_splitter.split_documents(documents)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=bge_embeddings,
        persist_directory=persist_dir
    )
    print(f"--- 数据库构建完成！文档块数量: {len(chunks)} ---")
    return vectorstore


def retrieve_by_surgery_type(vector_store: Chroma, query: str, surgery_type: str = None, top_k: int = 5) -> list:
    """基于手术类型定向检索相关文档
    
    Args:
        vector_store: 向量数据库实例
        query: 检索查询
        surgery_type: 手术类型，用于过滤或增强检索
        top_k: 返回结果数量
        
    Returns:
        检索到的文档列表
    """
    if not vector_store:
        return []
    
    retriever = vector_store.as_retriever(search_kwargs={"k": top_k})
    
    # 如果有手术类型，将其加入查询以增强相关性
    if surgery_type:
        enhanced_query = f"{surgery_type}术后 {query}"
    else:
        enhanced_query = query
    
    retrieved_docs = retriever.invoke(enhanced_query)
    
    return retrieved_docs


def format_retrieved_context(documents: list[Document]) -> str:
    """格式化检索到的文档内容"""
    if not documents:
        return ""
    
    context_parts = []
    for i, doc in enumerate(documents[:5], 1):
        context_parts.append(f"[参考文档{i}]")
        context_parts.append(doc.page_content)
        context_parts.append("")
    
    return "\n".join(context_parts)


def build_post_surgery_rag_index():
    """构建或加载术后护理文档的向量数据库"""
    _MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    post_surgery_care_dir = os.path.join(_MODULE_DIR, "post_surgery_care")
    post_surgery_persist_dir = os.path.join(_MODULE_DIR, "chroma_db_post_surgery")
    
    return build_or_load_rag_index(post_surgery_care_dir, post_surgery_persist_dir)


def build_general_rag_index():
    """构建或加载普通疾病文档的向量数据库"""
    return build_or_load_rag_index()
