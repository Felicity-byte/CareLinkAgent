import os
from typing import List, Optional, Dict, Any
from zhipuai import ZhipuAI

class ZhipuKnowledge:
    """智谱知识库检索模块"""

    DEFAULT_KNOWLEDGE_ID = "2041426353097789440"

    def __init__(self, api_key: str = None, knowledge_id: str = None):
        self.api_key = api_key or os.environ.get("ZHIPU_API_KEY") or os.environ.get("GLM_API_KEY")
        self.knowledge_id = knowledge_id or os.environ.get("ZHIPU_KNOWLEDGE_ID") or self.DEFAULT_KNOWLEDGE_ID
        self.client: Optional[ZhipuAI] = None
        self.is_available = False

        if self.api_key and self.knowledge_id:
            try:
                self.client = ZhipuAI(api_key=self.api_key)
                self.is_available = True
                print(f"[智谱知识库] 初始化成功，knowledge_id: {self.knowledge_id}")
            except Exception as e:
                print(f"[智谱知识库] 初始化失败: {e}")
    
    def retrieve(self, query: str, top_k: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        调用智谱知识库 API 检索文档
        
        Args:
            query: 检索查询
            top_k: 返回结果数量
            
        Returns:
            检索结果列表，每个元素包含 content 和 score
        """
        if not self.is_available or not self.client:
            return None
        
        try:
            response = self.client.embeddings.create(
                model="embedding-3",
                input=query
            )
            
            query_embedding = response.data[0].embedding
            
            knowledge_response = self.client.knowledge.search(
                knowledge_id=self.knowledge_id,
                embedding=query_embedding,
                top_k=top_k
            )
            
            results = []
            if hasattr(knowledge_response, 'results'):
                for item in knowledge_response.results:
                    results.append({
                        "content": item.get("content", ""),
                        "score": item.get("score", 0.0),
                        "source": item.get("source", "")
                    })
            
            return results if results else None
            
        except Exception as e:
            print(f"[智谱知识库] 检索失败: {e}")
            return None
    
    def is_relevant(self, query: str, threshold: float = 0.5) -> bool:
        """
        判断是否有相关文档
        
        Args:
            query: 查询内容
            threshold: 相关性阈值
            
        Returns:
            是否有相关文档
        """
        results = self.retrieve(query, top_k=1)
        if results and len(results) > 0:
            return results[0].get("score", 0.0) >= threshold
        return False


# 全局实例
zhipu_knowledge: Optional[ZhipuKnowledge] = None

def initialize_zhipu_knowledge():
    global zhipu_knowledge
    zhipu_knowledge = ZhipuKnowledge()
    return zhipu_knowledge
