"""RAGMemory — 检索增强记忆系统
Developer: Westlake Singularity Contributors
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional

class RAGMemory:
    """向量数据库记忆系统（轻量级实现）"""
    
    def __init__(self, storage_path: str = "./memory_store"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._documents: list[dict] = []
        self._index: dict[str, list[int]] = {}  # keyword → doc indices
    
    def add(self, content: str, metadata: dict = None, 
            doc_id: str = None) -> str:
        """添加文档"""
        doc_id = doc_id or hashlib.md5(content.encode()).hexdigest()[:12]
        doc = {
            "id": doc_id,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time(),
        }
        self._documents.append(doc)
        idx = len(self._documents) - 1
        
        # 简单关键词索引
        for word in set(content.lower().split()):
            if word not in self._index:
                self._index[word] = []
            self._index[word].append(idx)
        
        return doc_id
    
    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """关键词搜索 (后续替换为向量搜索)"""
        query_words = set(query.lower().split())
        scores = {}
        
        for word in query_words:
            for idx in self._index.get(word, []):
                scores[idx] = scores.get(idx, 0) + 1
        
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [self._documents[idx] for idx, score in ranked]
    
    def get(self, doc_id: str) -> Optional[dict]:
        for doc in self._documents:
            if doc["id"] == doc_id:
                return doc
        return None
    
    def save(self) -> None:
        """持久化"""
        data = {"docs": self._documents, "index": self._index}
        with open(self.storage_path / "memory.json", "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self) -> None:
        """加载"""
        path = self.storage_path / "memory.json"
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                self._documents = data["docs"]
                self._index = data["index"]
    
    def stats(self) -> dict:
        return {
            "total_documents": len(self._documents),
            "index_size": len(self._index),
            "storage_path": str(self.storage_path),
        }
