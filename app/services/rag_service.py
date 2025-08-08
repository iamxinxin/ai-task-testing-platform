import os
import openai
import anthropic
from typing import List, Optional, Dict, Any
import json
import numpy as np
import difflib
from app.schemas.test_schemas import RAGInput, RAGOutput

# 可选导入
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

class RAGService:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.embedding_model = None
        self.document_store = {}  # 简单的内存文档存储
        
        if os.getenv("OPENAI_API_KEY"):
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.openai_client = openai
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        
        # 初始化嵌入模型
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception:
                self.embedding_model = None
        else:
            self.embedding_model = None
    
    async def generate_answer(
        self,
        query: str,
        model_name: str,
        documents: Optional[List[str]] = None,
        top_k: int = 5
    ) -> RAGOutput:
        """生成基于检索的答案"""
        
        # 检索相关文档
        retrieved_docs = await self._retrieve_documents(query, documents, top_k)
        
        # 生成答案
        if model_name.startswith("gpt-"):
            return await self._generate_openai(query, model_name, retrieved_docs)
        elif model_name.startswith("claude-"):
            return await self._generate_anthropic(query, model_name, retrieved_docs)
        else:
            return await self._generate_mock(query, model_name, retrieved_docs)
    
    async def _retrieve_documents(
        self,
        query: str,
        documents: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """检索相关文档"""
        
        if not documents:
            # 从文档存储中检索
            documents = list(self.document_store.values())
        
        if not documents:
            return []
        
        if not self.embedding_model:
            # 如果没有嵌入模型，使用简单的关键词匹配
            return self._keyword_based_retrieval(query, documents, top_k)
        
        try:
            # 使用语义相似度检索
            query_embedding = self.embedding_model.encode([query])
            doc_embeddings = self.embedding_model.encode(documents)
            
            # 计算相似度
            similarities = np.dot(query_embedding, doc_embeddings.T)[0]
            
            # 获取top_k个最相似的文档
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            retrieved_docs = []
            for idx in top_indices:
                retrieved_docs.append({
                    "content": documents[idx],
                    "score": float(similarities[idx]),
                    "index": int(idx)
                })
            
            return retrieved_docs
            
        except Exception:
            # 如果语义检索失败，回退到关键词匹配
            return self._keyword_based_retrieval(query, documents, top_k)
    
    def _keyword_based_retrieval(
        self,
        query: str,
        documents: List[str],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """基于关键词的文档检索"""
        
        query_words = set(query.lower().split())
        doc_scores = []
        
        for idx, doc in enumerate(documents):
            doc_words = set(doc.lower().split())
            common_words = query_words.intersection(doc_words)
            score = len(common_words) / len(query_words) if query_words else 0
            doc_scores.append((idx, score, doc))
        
        # 按分数排序
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        retrieved_docs = []
        for idx, score, doc in doc_scores[:top_k]:
            retrieved_docs.append({
                "content": doc,
                "score": score,
                "index": idx
            })
        
        return retrieved_docs
    
    async def _generate_openai(
        self,
        query: str,
        model_name: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> RAGOutput:
        """使用OpenAI模型生成答案"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        # 构建上下文
        context = "\n\n".join([
            f"文档 {i+1}: {doc['content']}"
            for i, doc in enumerate(retrieved_docs)
        ])
        
        prompt = f"""基于以下文档内容回答用户问题：

文档内容:
{context}

用户问题: {query}

请基于提供的文档内容给出准确、详细的答案。如果文档中没有相关信息，请明确说明。"""
        
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的问答助手，请基于提供的文档内容回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            
            # 计算置信度
            confidence = self._calculate_answer_confidence(answer, retrieved_docs)
            
            return RAGOutput(
                answer=answer,
                retrieved_documents=retrieved_docs,
                confidence=confidence
            )
            
        except Exception as e:
            raise Exception(f"OpenAI RAG生成失败: {str(e)}")
    
    async def _generate_anthropic(
        self,
        query: str,
        model_name: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> RAGOutput:
        """使用Anthropic模型生成答案"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        context = "\n\n".join([
            f"文档 {i+1}: {doc['content']}"
            for i, doc in enumerate(retrieved_docs)
        ])
        
        prompt = f"""基于以下文档内容回答用户问题：

文档内容:
{context}

用户问题: {query}

请基于提供的文档内容给出准确、详细的答案。"""
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model_name,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            answer = response.content[0].text
            confidence = self._calculate_answer_confidence(answer, retrieved_docs)
            
            return RAGOutput(
                answer=answer,
                retrieved_documents=retrieved_docs,
                confidence=confidence
            )
            
        except Exception as e:
            raise Exception(f"Anthropic RAG生成失败: {str(e)}")
    
    async def _generate_mock(
        self,
        query: str,
        model_name: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> RAGOutput:
        """模拟RAG答案生成（用于演示）"""
        import random
        
        if retrieved_docs:
            # 基于检索到的文档生成模拟答案
            doc_content = retrieved_docs[0]['content'][:200]
            answer = f"基于检索到的文档，关于'{query}'的答案是：{doc_content}..."
        else:
            answer = f"抱歉，没有找到与'{query}'相关的文档信息。"
        
        confidence = random.uniform(0.6, 0.9) if retrieved_docs else 0.3
        
        return RAGOutput(
            answer=answer,
            retrieved_documents=retrieved_docs,
            confidence=confidence
        )
    
    def _calculate_answer_confidence(
        self,
        answer: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> float:
        """计算答案置信度"""
        
        if not retrieved_docs:
            return 0.3
        
        # 基于检索文档的平均分数
        avg_retrieval_score = np.mean([doc['score'] for doc in retrieved_docs])
        
        # 基于答案长度
        length_score = min(1.0, len(answer) / 200)
        
        # 综合置信度
        confidence = (avg_retrieval_score * 0.6 + length_score * 0.4)
        
        return min(0.95, max(0.1, confidence))
    
    async def add_documents(
        self,
        documents: List[str],
        collection_name: str = "default"
    ) -> List[str]:
        """添加文档到存储"""
        
        document_ids = []
        for i, doc in enumerate(documents):
            doc_id = f"{collection_name}_{len(self.document_store)}_{i}"
            self.document_store[doc_id] = doc
            document_ids.append(doc_id)
        
        return document_ids
    
    async def search_documents(
        self,
        query: str,
        collection_name: str = "default",
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """搜索文档"""
        
        # 过滤指定集合的文档
        collection_docs = [
            doc for doc_id, doc in self.document_store.items()
            if doc_id.startswith(collection_name)
        ]
        
        return await self._retrieve_documents(query, collection_docs, top_k)
    
    def evaluate(
        self,
        predicted: RAGOutput,
        expected: RAGOutput
    ) -> Dict[str, Any]:
        """评估RAG结果"""
        
        # 答案质量评估
        answer_similarity = self._calculate_similarity(
            predicted.answer,
            expected.answer
        )
        
        # 检索文档数量对比
        retrieved_count_diff = abs(
            len(predicted.retrieved_documents) - len(expected.retrieved_documents)
        )
        
        # 置信度差异
        confidence_diff = abs(predicted.confidence - expected.confidence)
        
        # 检索质量评估（如果有期望的检索文档）
        retrieval_quality = 0.0
        if expected.retrieved_documents:
            retrieval_quality = self._evaluate_retrieval_quality(
                predicted.retrieved_documents,
                expected.retrieved_documents
            )
        
        metrics = {
            "answer_quality": answer_similarity,
            "retrieval_quality": retrieval_quality,
            "retrieved_count_diff": retrieved_count_diff,
            "confidence_diff": confidence_diff,
            "predicted_retrieved_count": len(predicted.retrieved_documents),
            "expected_retrieved_count": len(expected.retrieved_documents),
            "predicted_confidence": predicted.confidence,
            "expected_confidence": expected.confidence
        }
        
        return metrics
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        if text1 == text2:
            return 1.0
        
        matcher = difflib.SequenceMatcher(None, text1.lower(), text2.lower())
        return matcher.ratio()
    
    def _evaluate_retrieval_quality(
        self,
        predicted_docs: List[Dict[str, Any]],
        expected_docs: List[Dict[str, Any]]
    ) -> float:
        """评估检索质量"""
        
        if not expected_docs:
            return 0.0
        
        # 计算检索到的文档与期望文档的重叠度
        predicted_contents = set([doc['content'] for doc in predicted_docs])
        expected_contents = set([doc['content'] for doc in expected_docs])
        
        if not expected_contents:
            return 0.0
        
        intersection = predicted_contents.intersection(expected_contents)
        return len(intersection) / len(expected_contents)