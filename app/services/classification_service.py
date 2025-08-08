import os
import openai
import anthropic
from typing import List, Optional, Dict, Any
import json
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from app.schemas.test_schemas import ClassificationInput, ClassificationOutput

class ClassificationService:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # 初始化API客户端
        if os.getenv("OPENAI_API_KEY"):
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.openai_client = openai
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
    
    async def classify(
        self,
        text: str,
        model_name: str,
        labels: Optional[List[str]] = None
    ) -> ClassificationOutput:
        """执行文本分类任务"""
        
        if model_name.startswith("gpt-"):
            return await self._classify_openai(text, model_name, labels)
        elif model_name.startswith("claude-"):
            return await self._classify_anthropic(text, model_name, labels)
        elif model_name.startswith("huggingface/"):
            return await self._classify_huggingface(text, model_name, labels)
        else:
            return await self._classify_mock(text, model_name, labels)
    
    async def _classify_openai(
        self,
        text: str,
        model_name: str,
        labels: Optional[List[str]] = None
    ) -> ClassificationOutput:
        """使用OpenAI模型进行分类"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        # 构建提示词
        if labels:
            prompt = f"""请对以下文本进行分类，从给定的标签中选择最合适的一个：

文本: {text}

可选标签: {', '.join(labels)}

请返回JSON格式的结果，包含predicted_label和confidence字段。"""
        else:
            prompt = f"""请对以下文本进行情感分析分类：

文本: {text}

请从以下标签中选择：positive, negative, neutral

请返回JSON格式的结果，包含predicted_label和confidence字段。"""
        
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的文本分类助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            # 尝试解析JSON结果
            try:
                result_json = json.loads(result_text)
                predicted_label = result_json.get("predicted_label", "unknown")
                confidence = result_json.get("confidence", 0.5)
            except json.JSONDecodeError:
                # 如果无法解析JSON，尝试从文本中提取标签
                predicted_label = self._extract_label_from_text(result_text, labels)
                confidence = 0.5
            
            return ClassificationOutput(
                predicted_label=predicted_label,
                confidence=confidence,
                probabilities={predicted_label: confidence} if labels else None
            )
            
        except Exception as e:
            raise Exception(f"OpenAI分类失败: {str(e)}")
    
    async def _classify_anthropic(
        self,
        text: str,
        model_name: str,
        labels: Optional[List[str]] = None
    ) -> ClassificationOutput:
        """使用Anthropic模型进行分类"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        # 构建提示词
        if labels:
            prompt = f"""请对以下文本进行分类，从给定的标签中选择最合适的一个：

文本: {text}

可选标签: {', '.join(labels)}

请返回JSON格式的结果，包含predicted_label和confidence字段。"""
        else:
            prompt = f"""请对以下文本进行情感分析分类：

文本: {text}

请从以下标签中选择：positive, negative, neutral

请返回JSON格式的结果，包含predicted_label和confidence字段。"""
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model_name,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.content[0].text
            
            # 尝试解析JSON结果
            try:
                result_json = json.loads(result_text)
                predicted_label = result_json.get("predicted_label", "unknown")
                confidence = result_json.get("confidence", 0.5)
            except json.JSONDecodeError:
                predicted_label = self._extract_label_from_text(result_text, labels)
                confidence = 0.5
            
            return ClassificationOutput(
                predicted_label=predicted_label,
                confidence=confidence,
                probabilities={predicted_label: confidence} if labels else None
            )
            
        except Exception as e:
            raise Exception(f"Anthropic分类失败: {str(e)}")
    
    async def _classify_huggingface(
        self,
        text: str,
        model_name: str,
        labels: Optional[List[str]] = None
    ) -> ClassificationOutput:
        """使用HuggingFace模型进行分类"""
        # 这里可以集成HuggingFace的transformers库
        # 为了演示，我们返回模拟结果
        return await self._classify_mock(text, model_name, labels)
    
    async def _classify_mock(
        self,
        text: str,
        model_name: str,
        labels: Optional[List[str]] = None
    ) -> ClassificationOutput:
        """模拟分类结果（用于演示）"""
        import random
        
        if labels:
            predicted_label = random.choice(labels)
        else:
            predicted_label = random.choice(["positive", "negative", "neutral"])
        
        confidence = random.uniform(0.6, 0.95)
        
        probabilities = {}
        if labels:
            remaining_prob = 1.0 - confidence
            for label in labels:
                if label == predicted_label:
                    probabilities[label] = confidence
                else:
                    probabilities[label] = remaining_prob / (len(labels) - 1)
        
        return ClassificationOutput(
            predicted_label=predicted_label,
            confidence=confidence,
            probabilities=probabilities
        )
    
    def _extract_label_from_text(self, text: str, labels: Optional[List[str]] = None) -> str:
        """从文本中提取标签"""
        text_lower = text.lower()
        
        if labels:
            for label in labels:
                if label.lower() in text_lower:
                    return label
            return labels[0]  # 默认返回第一个标签
        else:
            # 情感分析默认标签
            if "positive" in text_lower or "积极" in text_lower:
                return "positive"
            elif "negative" in text_lower or "消极" in text_lower:
                return "negative"
            else:
                return "neutral"
    
    def evaluate(
        self,
        predicted: ClassificationOutput,
        expected: ClassificationOutput
    ) -> Dict[str, Any]:
        """评估分类结果"""
        
        # 基本准确性
        accuracy = 1.0 if predicted.predicted_label == expected.predicted_label else 0.0
        
        # 置信度差异
        confidence_diff = abs(predicted.confidence - expected.confidence)
        
        metrics = {
            "accuracy": accuracy,
            "predicted_label": predicted.predicted_label,
            "expected_label": expected.predicted_label,
            "confidence_diff": confidence_diff,
            "predicted_confidence": predicted.confidence,
            "expected_confidence": expected.confidence
        }
        
        return metrics
    
    def batch_evaluate(
        self,
        predictions: List[ClassificationOutput],
        expected: List[ClassificationOutput]
    ) -> Dict[str, Any]:
        """批量评估分类结果"""
        
        if len(predictions) != len(expected):
            raise ValueError("预测结果和期望结果数量不匹配")
        
        predicted_labels = [p.predicted_label for p in predictions]
        expected_labels = [e.predicted_label for e in expected]
        
        # 计算准确率
        accuracy = accuracy_score(expected_labels, predicted_labels)
        
        # 计算精确率、召回率、F1分数
        precision, recall, f1, support = precision_recall_fscore_support(
            expected_labels, predicted_labels, average='weighted'
        )
        
        # 计算置信度相关指标
        confidence_diffs = [
            abs(p.confidence - e.confidence) 
            for p, e in zip(predictions, expected)
        ]
        avg_confidence_diff = np.mean(confidence_diffs)
        
        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "avg_confidence_diff": avg_confidence_diff,
            "total_samples": len(predictions)
        }