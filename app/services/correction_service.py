import os
import openai
import anthropic
from typing import Dict, Any
import json
import difflib
from app.schemas.test_schemas import CorrectionInput, CorrectionOutput

class CorrectionService:
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
    
    async def correct(
        self,
        text: str,
        model_name: str,
        correction_type: str = "grammar"
    ) -> CorrectionOutput:
        """执行文本纠错任务"""
        
        if model_name.startswith("gpt-"):
            return await self._correct_openai(text, model_name, correction_type)
        elif model_name.startswith("claude-"):
            return await self._correct_anthropic(text, model_name, correction_type)
        else:
            return await self._correct_mock(text, model_name, correction_type)
    
    async def _correct_openai(
        self,
        text: str,
        model_name: str,
        correction_type: str
    ) -> CorrectionOutput:
        """使用OpenAI模型进行纠错"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        correction_prompts = {
            "grammar": "请纠正以下文本的语法错误，保持原意不变：",
            "spelling": "请纠正以下文本的拼写错误：",
            "style": "请改善以下文本的表达风格，使其更加流畅自然："
        }
        
        prompt = f"""{correction_prompts.get(correction_type, correction_prompts['grammar'])}

原文: {text}

请返回JSON格式的结果，包含以下字段：
- corrected_text: 纠错后的文本
- corrections: 修改列表，每个修改包含original、corrected、type、position等信息
- confidence: 纠错的置信度(0-1)"""
        
        try:
            response = await self.openai_client.ChatCompletion.acreate(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一个专业的文本纠错助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content
            
            try:
                result_json = json.loads(result_text)
                corrected_text = result_json.get("corrected_text", text)
                corrections = result_json.get("corrections", [])
                confidence = result_json.get("confidence", 0.8)
            except json.JSONDecodeError:
                # 如果无法解析JSON，尝试从文本中提取纠错结果
                corrected_text = self._extract_corrected_text(result_text, text)
                corrections = self._generate_corrections(text, corrected_text)
                confidence = 0.7
            
            return CorrectionOutput(
                corrected_text=corrected_text,
                corrections=corrections,
                confidence=confidence
            )
            
        except Exception as e:
            raise Exception(f"OpenAI纠错失败: {str(e)}")
    
    async def _correct_anthropic(
        self,
        text: str,
        model_name: str,
        correction_type: str
    ) -> CorrectionOutput:
        """使用Anthropic模型进行纠错"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        correction_prompts = {
            "grammar": "请纠正以下文本的语法错误，保持原意不变：",
            "spelling": "请纠正以下文本的拼写错误：",
            "style": "请改善以下文本的表达风格，使其更加流畅自然："
        }
        
        prompt = f"""{correction_prompts.get(correction_type, correction_prompts['grammar'])}

原文: {text}

请返回JSON格式的结果，包含以下字段：
- corrected_text: 纠错后的文本
- corrections: 修改列表
- confidence: 纠错的置信度(0-1)"""
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model_name,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.content[0].text
            
            try:
                result_json = json.loads(result_text)
                corrected_text = result_json.get("corrected_text", text)
                corrections = result_json.get("corrections", [])
                confidence = result_json.get("confidence", 0.8)
            except json.JSONDecodeError:
                corrected_text = self._extract_corrected_text(result_text, text)
                corrections = self._generate_corrections(text, corrected_text)
                confidence = 0.7
            
            return CorrectionOutput(
                corrected_text=corrected_text,
                corrections=corrections,
                confidence=confidence
            )
            
        except Exception as e:
            raise Exception(f"Anthropic纠错失败: {str(e)}")
    
    async def _correct_mock(
        self,
        text: str,
        model_name: str,
        correction_type: str
    ) -> CorrectionOutput:
        """模拟纠错结果（用于演示）"""
        import random
        
        # 简单的模拟纠错
        corrections = []
        corrected_text = text
        
        # 模拟一些常见的纠错
        common_errors = {
            "teh": "the",
            "recieve": "receive",
            "seperate": "separate",
            "occured": "occurred"
        }
        
        for wrong, correct in common_errors.items():
            if wrong in text.lower():
                corrected_text = corrected_text.replace(wrong, correct)
                corrections.append({
                    "original": wrong,
                    "corrected": correct,
                    "type": "spelling",
                    "position": text.lower().find(wrong)
                })
        
        confidence = random.uniform(0.7, 0.95)
        
        return CorrectionOutput(
            corrected_text=corrected_text,
            corrections=corrections,
            confidence=confidence
        )
    
    def _extract_corrected_text(self, result_text: str, original_text: str) -> str:
        """从结果文本中提取纠错后的文本"""
        lines = result_text.split('\n')
        for line in lines:
            if '纠错后' in line or 'corrected' in line.lower():
                # 尝试提取纠错后的文本
                parts = line.split(':', 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        return original_text  # 如果无法提取，返回原文
    
    def _generate_corrections(self, original: str, corrected: str) -> list:
        """生成修改列表"""
        corrections = []
        
        # 使用difflib比较文本差异
        diff = list(difflib.unified_diff(
            original.split(),
            corrected.split(),
            lineterm=''
        ))
        
        for line in diff:
            if line.startswith('-'):
                # 删除的词
                word = line[1:].strip()
                if word:
                    corrections.append({
                        "original": word,
                        "corrected": "",
                        "type": "deletion",
                        "position": original.find(word)
                    })
            elif line.startswith('+'):
                # 添加的词
                word = line[1:].strip()
                if word:
                    corrections.append({
                        "original": "",
                        "corrected": word,
                        "type": "addition",
                        "position": -1
                    })
        
        return corrections
    
    def evaluate(
        self,
        predicted: CorrectionOutput,
        expected: CorrectionOutput
    ) -> Dict[str, Any]:
        """评估纠错结果"""
        
        # 计算文本相似度
        similarity_score = self._calculate_similarity(
            predicted.corrected_text,
            expected.corrected_text
        )
        
        # 计算纠错数量匹配度
        correction_count_diff = abs(
            len(predicted.corrections) - len(expected.corrections)
        )
        
        # 置信度差异
        confidence_diff = abs(predicted.confidence - expected.confidence)
        
        metrics = {
            "similarity_score": similarity_score,
            "correction_count_diff": correction_count_diff,
            "confidence_diff": confidence_diff,
            "predicted_corrections": len(predicted.corrections),
            "expected_corrections": len(expected.corrections),
            "predicted_confidence": predicted.confidence,
            "expected_confidence": expected.confidence
        }
        
        return metrics
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if text1 == text2:
            return 1.0
        
        # 使用序列匹配器计算相似度
        matcher = difflib.SequenceMatcher(None, text1, text2)
        return matcher.ratio()