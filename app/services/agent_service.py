import os
import openai
import anthropic
from typing import List, Optional, Dict, Any
import json
import requests
import difflib
from app.schemas.test_schemas import AgentInput, AgentOutput

class AgentService:
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
        
        # 定义可用工具
        self.available_tools = {
            "web_search": self._web_search,
            "calculator": self._calculator,
            "text_analyzer": self._text_analyzer,
            "file_reader": self._file_reader,
            "api_caller": self._api_caller
        }
    
    async def execute_task(
        self,
        task: str,
        model_name: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None
    ) -> AgentOutput:
        """执行Agent任务"""
        
        if model_name.startswith("gpt-"):
            return await self._execute_openai(task, model_name, context, tools)
        elif model_name.startswith("claude-"):
            return await self._execute_anthropic(task, model_name, context, tools)
        else:
            return await self._execute_mock(task, model_name, context, tools)
    
    async def _execute_openai(
        self,
        task: str,
        model_name: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None
    ) -> AgentOutput:
        """使用OpenAI模型执行Agent任务"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        # 构建系统提示
        system_prompt = self._build_system_prompt(tools)
        
        # 构建用户消息
        user_message = self._build_user_message(task, context)
        
        actions_taken = []
        result = ""
        
        try:
            # 第一步：分析任务并制定计划
            response = await self.openai_client.ChatCompletion.acreate(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            agent_response = response.choices[0].message.content
            
            # 解析Agent的响应，提取工具调用
            tool_calls = self._parse_tool_calls(agent_response)
            
            # 执行工具调用
            for tool_call in tool_calls:
                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("args", {})
                
                if tool_name in self.available_tools and (not tools or tool_name in tools):
                    try:
                        tool_result = await self.available_tools[tool_name](**tool_args)
                        actions_taken.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": tool_result,
                            "status": "success"
                        })
                    except Exception as e:
                        actions_taken.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "error": str(e),
                            "status": "failed"
                        })
            
            # 如果有工具调用结果，让Agent综合结果
            if actions_taken:
                tool_results_text = "\n".join([
                    f"工具 {action['tool']} 的结果: {action.get('result', action.get('error'))}"
                    for action in actions_taken
                ])
                
                final_response = await self.openai_client.ChatCompletion.acreate(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": agent_response},
                        {"role": "user", "content": f"工具执行结果:\n{tool_results_text}\n\n请基于这些结果给出最终答案。"}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                result = final_response.choices[0].message.content
            else:
                result = agent_response
            
            # 计算置信度
            confidence = self._calculate_confidence(result, actions_taken)
            
            return AgentOutput(
                result=result,
                actions_taken=actions_taken,
                confidence=confidence
            )
            
        except Exception as e:
            raise Exception(f"OpenAI Agent执行失败: {str(e)}")
    
    async def _execute_anthropic(
        self,
        task: str,
        model_name: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None
    ) -> AgentOutput:
        """使用Anthropic模型执行Agent任务"""
        if not self.anthropic_client:
            raise ValueError("Anthropic API key not configured")
        
        system_prompt = self._build_system_prompt(tools)
        user_message = self._build_user_message(task, context)
        
        full_prompt = f"{system_prompt}\n\n{user_message}"
        
        actions_taken = []
        
        try:
            response = await self.anthropic_client.messages.create(
                model=model_name,
                max_tokens=1500,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            agent_response = response.content[0].text
            
            # 解析和执行工具调用
            tool_calls = self._parse_tool_calls(agent_response)
            
            for tool_call in tool_calls:
                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("args", {})
                
                if tool_name in self.available_tools and (not tools or tool_name in tools):
                    try:
                        tool_result = await self.available_tools[tool_name](**tool_args)
                        actions_taken.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "result": tool_result,
                            "status": "success"
                        })
                    except Exception as e:
                        actions_taken.append({
                            "tool": tool_name,
                            "args": tool_args,
                            "error": str(e),
                            "status": "failed"
                        })
            
            result = agent_response
            confidence = self._calculate_confidence(result, actions_taken)
            
            return AgentOutput(
                result=result,
                actions_taken=actions_taken,
                confidence=confidence
            )
            
        except Exception as e:
            raise Exception(f"Anthropic Agent执行失败: {str(e)}")
    
    async def _execute_mock(
        self,
        task: str,
        model_name: str,
        context: Optional[Dict[str, Any]] = None,
        tools: Optional[List[str]] = None
    ) -> AgentOutput:
        """模拟Agent任务执行（用于演示）"""
        import random
        
        actions_taken = []
        
        # 模拟使用一些工具
        if tools:
            for tool in tools[:2]:  # 最多使用2个工具
                if tool in self.available_tools:
                    try:
                        # 模拟工具调用
                        if tool == "calculator":
                            tool_result = await self.available_tools[tool](expression="2+2")
                        elif tool == "text_analyzer":
                            tool_result = await self.available_tools[tool](text=task[:100])
                        else:
                            tool_result = f"模拟 {tool} 工具的执行结果"
                        
                        actions_taken.append({
                            "tool": tool,
                            "args": {"mock": True},
                            "result": tool_result,
                            "status": "success"
                        })
                    except Exception as e:
                        actions_taken.append({
                            "tool": tool,
                            "args": {"mock": True},
                            "error": str(e),
                            "status": "failed"
                        })
        
        # 生成模拟结果
        result = f"我已经分析了任务：'{task[:50]}...'，并使用了 {len(actions_taken)} 个工具来完成这个任务。基于分析结果，我的建议是..."
        
        confidence = random.uniform(0.7, 0.95)
        
        return AgentOutput(
            result=result,
            actions_taken=actions_taken,
            confidence=confidence
        )
    
    def _build_system_prompt(self, tools: Optional[List[str]] = None) -> str:
        """构建系统提示"""
        
        base_prompt = """你是一个智能AI助手，能够使用各种工具来完成复杂任务。

你的工作流程：
1. 分析用户的任务需求
2. 确定需要使用的工具
3. 按顺序执行工具调用
4. 综合结果给出最终答案

可用工具："""
        
        if tools:
            for tool in tools:
                if tool in self.available_tools:
                    base_prompt += f"\n- {tool}: {self._get_tool_description(tool)}"
        else:
            for tool_name in self.available_tools:
                base_prompt += f"\n- {tool_name}: {self._get_tool_description(tool_name)}"
        
        base_prompt += """

工具调用格式：
[TOOL_CALL]
{
    "tool": "工具名称",
    "args": {
        "参数名": "参数值"
    }
}
[/TOOL_CALL]

请根据任务需求选择合适的工具，并按照上述格式进行调用。"""
        
        return base_prompt
    
    def _build_user_message(self, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """构建用户消息"""
        
        message = f"任务: {task}"
        
        if context:
            message += f"\n\n上下文信息:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
        
        message += "\n\n请分析这个任务，使用必要的工具，并给出详细的解决方案。"
        
        return message
    
    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """解析工具调用"""
        
        tool_calls = []
        
        # 查找工具调用标记
        import re
        pattern = r'\[TOOL_CALL\](.*?)\[/TOOL_CALL\]'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                tool_call = json.loads(match.strip())
                tool_calls.append(tool_call)
            except json.JSONDecodeError:
                continue
        
        return tool_calls
    
    def _get_tool_description(self, tool_name: str) -> str:
        """获取工具描述"""
        
        descriptions = {
            "web_search": "搜索网络信息",
            "calculator": "执行数学计算",
            "text_analyzer": "分析文本内容",
            "file_reader": "读取文件内容",
            "api_caller": "调用外部API"
        }
        
        return descriptions.get(tool_name, "未知工具")
    
    def _calculate_confidence(self, result: str, actions_taken: List[Dict[str, Any]]) -> float:
        """计算置信度"""
        
        base_confidence = 0.7
        
        # 基于工具使用情况调整置信度
        if actions_taken:
            successful_actions = sum(1 for action in actions_taken if action.get("status") == "success")
            total_actions = len(actions_taken)
            
            if total_actions > 0:
                success_rate = successful_actions / total_actions
                base_confidence += (success_rate - 0.5) * 0.3
        
        # 基于结果长度调整置信度
        if len(result) > 100:
            base_confidence += 0.1
        
        return min(0.95, max(0.1, base_confidence))
    
    # 工具实现
    async def _web_search(self, query: str, num_results: int = 5) -> str:
        """网络搜索工具（模拟）"""
        return f"搜索 '{query}' 的结果：找到 {num_results} 个相关结果（模拟数据）"
    
    async def _calculator(self, expression: str) -> str:
        """计算器工具"""
        try:
            # 安全的数学表达式计算
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return f"{expression} = {result}"
            else:
                return "表达式包含不允许的字符"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    async def _text_analyzer(self, text: str) -> str:
        """文本分析工具"""
        word_count = len(text.split())
        char_count = len(text)
        
        return f"文本分析结果：字符数 {char_count}，单词数 {word_count}"
    
    async def _file_reader(self, file_path: str) -> str:
        """文件读取工具（模拟）"""
        return f"读取文件 '{file_path}' 的内容（模拟数据）"
    
    async def _api_caller(self, url: str, method: str = "GET", data: dict = None) -> str:
        """API调用工具（模拟）"""
        return f"调用API {method} {url} 的结果（模拟数据）"
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """获取可用工具列表"""
        
        return [
            {
                "name": tool_name,
                "description": self._get_tool_description(tool_name)
            }
            for tool_name in self.available_tools
        ]
    
    def evaluate(
        self,
        predicted: AgentOutput,
        expected: AgentOutput
    ) -> Dict[str, Any]:
        """评估Agent执行结果"""
        
        # 任务完成度评估
        task_completion_score = self._calculate_similarity(
            predicted.result,
            expected.result
        )
        
        # 工具使用评估
        predicted_tools = set([action.get("tool") for action in predicted.actions_taken])
        expected_tools = set([action.get("tool") for action in expected.actions_taken])
        
        tool_usage_score = 0.0
        if expected_tools:
            tool_overlap = predicted_tools.intersection(expected_tools)
            tool_usage_score = len(tool_overlap) / len(expected_tools)
        
        # 执行步骤数量对比
        action_count_diff = abs(len(predicted.actions_taken) - len(expected.actions_taken))
        
        # 置信度差异
        confidence_diff = abs(predicted.confidence - expected.confidence)
        
        metrics = {
            "task_completion_score": task_completion_score,
            "tool_usage_score": tool_usage_score,
            "action_count_diff": action_count_diff,
            "confidence_diff": confidence_diff,
            "predicted_actions": len(predicted.actions_taken),
            "expected_actions": len(expected.actions_taken),
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