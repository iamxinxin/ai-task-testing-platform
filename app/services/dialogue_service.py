import os
import openai
import anthropic
from typing import List, Optional, Dict, Any
import json
import difflib
from app.schemas.test_schemas import DialogueInput, DialogueOutput

class DialogueService:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        if os.getenv("OPENAI_API_KEY"):
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.openai_client = openai
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
    
    async def generate_response(
        self,
        message: str,
        model_name: str,
        context: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[str] = None
    ) -> DialogueOutput:
        """生成对话响应"""
        
        if model_name.startswith("gpt-"):
            return await self._generate_openai(message, model_name, context, user_id)
        elif model_name.startswith("claude-"):
            return await self._generate_anthropic(message, model_name, context, user_id)
        else:
            return await self._generate_mock(message, model_name, context, user_id)
    
    async def _generate_openai(
        self,
        message: str,
        model_name: str,
        context: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[str] = None
    ) -> DialogueOutput:
        """使用OpenAI模型生成对话响应"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        # 构建消息历史
        messages = [
            {"role": "system", "content": "你是一个有用、友善、诚实的AI助手。请根据用户的问题提供准确、有帮助的回答。"}
        ]
        
        # 添加上下文
        context_used = False
        if context:
            context_used = True
            for ctx in context[-5:]:  # 只使用最近5轮对话
                if ctx.get("role") and ctx.get("content"):
                    messages.append({
                        "role": ctx["role"],
                        "content": ctx["content"]
                    })
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content
            
            # 计算置信度（基于响应长度和完整性）
            confidence = min(0.9, len(response_text) / 100 + 0.5)
            
            return DialogueOutput(
                response=response_text,
                confidence=confidence,
                context_used=context_used
            )
            
        except Exception as e:
            raise Exception(f"OpenAI对话生成失败: {str(e)}")
    
    async def _generate_anthropic(
        self,
        message: str,
        model_name: str,
        context: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[str] = None
    ) -> DialogueOutput:
        """使用Anthropic模型生成对话响应"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        # 构建对话内容
        conversation_text = message
        context_used = False
        
        if context:
            context_used = True
            context_text = "\n".join([
                f"{ctx.get('role', 'user')}: {ctx.get('content', '')}"
                for ctx in context[-5:]
            ])
            conversation_text = f"对话历史:\n{context_text}\n\n当前用户消息: {message}"
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model_name,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": conversation_text}
                ]
            )
            
            response_text = response.content[0].text
            confidence = min(0.9, len(response_text) / 100 + 0.5)
            
            return DialogueOutput(
                response=response_text,
                confidence=confidence,
                context_used=context_used
            )
            
        except Exception as e:
            raise Exception(f"Anthropic对话生成失败: {str(e)}")
    
    async def _generate_mock(
        self,
        message: str,
        model_name: str,
        context: Optional[List[Dict[str, str]]] = None,
        user_id: Optional[str] = None
    ) -> DialogueOutput:
        """模拟对话响应（用于演示）"""
        import random
        
        # 简单的模拟响应
        mock_responses = [
            f"我理解您关于'{message[:20]}...'的问题。让我为您详细解答。",
            f"关于您提到的'{message[:20]}...'，我认为这是一个很好的问题。",
            f"感谢您的提问。对于'{message[:20]}...'这个话题，我有以下看法：",
            f"这是一个有趣的问题。关于'{message[:20]}...'，我建议您考虑以下几点：",
        ]
        
        response = random.choice(mock_responses)
        confidence = random.uniform(0.7, 0.95)
        context_used = context is not None and len(context) > 0
        
        return DialogueOutput(
            response=response,
            confidence=confidence,
            context_used=context_used
        )
    
    def evaluate(
        self,
        predicted: DialogueOutput,
        expected: DialogueOutput
    ) -> Dict[str, Any]:
        """评估对话响应质量"""
        
        # 计算响应相似度
        relevance_score = self._calculate_similarity(
            predicted.response,
            expected.response
        )
        
        # 计算响应长度差异
        length_diff = abs(len(predicted.response) - len(expected.response))
        length_ratio = min(len(predicted.response), len(expected.response)) / max(len(predicted.response), len(expected.response))
        
        # 置信度差异
        confidence_diff = abs(predicted.confidence - expected.confidence)
        
        # 上下文使用一致性
        context_consistency = 1.0 if predicted.context_used == expected.context_used else 0.0
        
        metrics = {
            "relevance_score": relevance_score,
            "length_diff": length_diff,
            "length_ratio": length_ratio,
            "confidence_diff": confidence_diff,
            "context_consistency": context_consistency,
            "predicted_length": len(predicted.response),
            "expected_length": len(expected.response),
            "predicted_confidence": predicted.confidence,
            "expected_confidence": expected.confidence
        }
        
        return metrics
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if text1 == text2:
            return 1.0
        
        # 使用序列匹配器计算相似度
        matcher = difflib.SequenceMatcher(None, text1.lower(), text2.lower())
        return matcher.ratio()
    
    def calculate_dialogue_quality(
        self,
        response: str,
        message: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, float]:
        """计算对话质量指标"""
        
        metrics = {}
        
        # 响应长度合理性
        response_length = len(response)
        if 10 <= response_length <= 500:
            metrics["length_score"] = 1.0
        elif response_length < 10:
            metrics["length_score"] = response_length / 10
        else:
            metrics["length_score"] = max(0.5, 500 / response_length)
        
        # 关键词匹配度
        message_words = set(message.lower().split())
        response_words = set(response.lower().split())
        common_words = message_words.intersection(response_words)
        
        if message_words:
            metrics["keyword_match"] = len(common_words) / len(message_words)
        else:
            metrics["keyword_match"] = 0.0
        
        # 上下文相关性（如果有上下文）
        if context:
            context_text = " ".join([ctx.get("content", "") for ctx in context])
            context_words = set(context_text.lower().split())
            context_response_common = context_words.intersection(response_words)
            
            if context_words:
                metrics["context_relevance"] = len(context_response_common) / len(context_words)
            else:
                metrics["context_relevance"] = 0.0
        else:
            metrics["context_relevance"] = 0.0
        
        return metrics