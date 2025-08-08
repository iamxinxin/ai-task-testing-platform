#!/usr/bin/env python3
"""
初始化示例数据
"""

import asyncio
import json
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.test_models import Base, TestCase, TestSuite, Model

def create_sample_data():
    """创建示例数据"""
    
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 创建示例模型配置
        models = [
            Model(
                name="mock-classifier",
                model_type="mock",
                config={"temperature": 0.7},
                api_endpoint="http://localhost:8000/mock"
            ),
            Model(
                name="gpt-3.5-turbo",
                model_type="openai",
                config={"temperature": 0.3, "max_tokens": 1000},
                api_endpoint="https://api.openai.com/v1/chat/completions"
            ),
            Model(
                name="claude-3-sonnet",
                model_type="anthropic",
                config={"max_tokens": 1000},
                api_endpoint="https://api.anthropic.com/v1/messages"
            )
        ]
        
        for model in models:
            existing = db.query(Model).filter(Model.name == model.name).first()
            if not existing:
                db.add(model)
        
        # 创建分类任务示例测试用例
        classification_cases = [
            {
                "name": "情感分析-积极评论",
                "task_type": "classification",
                "description": "测试对积极评论的情感分析",
                "input_data": {
                    "text": "这个产品真的很棒，我非常喜欢！",
                    "labels": ["positive", "negative", "neutral"]
                },
                "expected_output": {
                    "predicted_label": "positive",
                    "confidence": 0.9
                }
            },
            {
                "name": "情感分析-消极评论",
                "task_type": "classification",
                "description": "测试对消极评论的情感分析",
                "input_data": {
                    "text": "这个产品质量很差，完全不值这个价格。",
                    "labels": ["positive", "negative", "neutral"]
                },
                "expected_output": {
                    "predicted_label": "negative",
                    "confidence": 0.85
                }
            },
            {
                "name": "文本分类-技术文档",
                "task_type": "classification",
                "description": "测试技术文档的分类",
                "input_data": {
                    "text": "本文档介绍了如何使用Python进行机器学习模型的训练和部署。",
                    "labels": ["技术", "商业", "娱乐", "新闻"]
                },
                "expected_output": {
                    "predicted_label": "技术",
                    "confidence": 0.8
                }
            }
        ]
        
        for case_data in classification_cases:
            existing = db.query(TestCase).filter(TestCase.name == case_data["name"]).first()
            if not existing:
                test_case = TestCase(**case_data)
                db.add(test_case)
        
        # 创建纠错任务示例测试用例
        correction_cases = [
            {
                "name": "语法纠错-时态错误",
                "task_type": "correction",
                "description": "测试时态错误的纠正",
                "input_data": {
                    "text": "I have went to the store yesterday.",
                    "correction_type": "grammar"
                },
                "expected_output": {
                    "corrected_text": "I went to the store yesterday.",
                    "corrections": [
                        {
                            "original": "have went",
                            "corrected": "went",
                            "type": "grammar",
                            "position": 2
                        }
                    ],
                    "confidence": 0.9
                }
            },
            {
                "name": "拼写纠错-常见错误",
                "task_type": "correction",
                "description": "测试常见拼写错误的纠正",
                "input_data": {
                    "text": "I recieved your mesage yesterday.",
                    "correction_type": "spelling"
                },
                "expected_output": {
                    "corrected_text": "I received your message yesterday.",
                    "corrections": [
                        {
                            "original": "recieved",
                            "corrected": "received",
                            "type": "spelling",
                            "position": 2
                        },
                        {
                            "original": "mesage",
                            "corrected": "message",
                            "type": "spelling",
                            "position": 8
                        }
                    ],
                    "confidence": 0.95
                }
            }
        ]
        
        for case_data in correction_cases:
            existing = db.query(TestCase).filter(TestCase.name == case_data["name"]).first()
            if not existing:
                test_case = TestCase(**case_data)
                db.add(test_case)
        
        # 创建对话任务示例测试用例
        dialogue_cases = [
            {
                "name": "问候对话",
                "task_type": "dialogue",
                "description": "测试基本问候对话",
                "input_data": {
                    "message": "你好，今天天气怎么样？",
                    "context": []
                },
                "expected_output": {
                    "response": "你好！我是AI助手，很抱歉我无法获取实时天气信息。建议您查看天气应用或网站获取准确的天气预报。",
                    "confidence": 0.8,
                    "context_used": False
                }
            },
            {
                "name": "技术咨询对话",
                "task_type": "dialogue",
                "description": "测试技术问题咨询",
                "input_data": {
                    "message": "如何学习机器学习？",
                    "context": []
                },
                "expected_output": {
                    "response": "学习机器学习建议从以下几个方面开始：1. 掌握数学基础（线性代数、概率统计）；2. 学习Python编程；3. 了解机器学习算法原理；4. 实践项目经验；5. 持续学习新技术。",
                    "confidence": 0.85,
                    "context_used": False
                }
            }
        ]
        
        for case_data in dialogue_cases:
            existing = db.query(TestCase).filter(TestCase.name == case_data["name"]).first()
            if not existing:
                test_case = TestCase(**case_data)
                db.add(test_case)
        
        # 创建RAG任务示例测试用例
        rag_cases = [
            {
                "name": "技术文档问答",
                "task_type": "rag",
                "description": "基于技术文档的问答",
                "input_data": {
                    "query": "什么是机器学习？",
                    "documents": [
                        "机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。",
                        "深度学习是机器学习的一个子集，使用神经网络来模拟人脑的工作方式。",
                        "监督学习是机器学习的一种方法，使用标记的训练数据来训练模型。"
                    ],
                    "top_k": 3
                },
                "expected_output": {
                    "answer": "机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。这是一种让计算机系统通过经验自动改进性能的方法。",
                    "retrieved_documents": [
                        {
                            "content": "机器学习是人工智能的一个分支，它使计算机能够在没有明确编程的情况下学习。",
                            "score": 0.95,
                            "index": 0
                        }
                    ],
                    "confidence": 0.9
                }
            }
        ]
        
        for case_data in rag_cases:
            existing = db.query(TestCase).filter(TestCase.name == case_data["name"]).first()
            if not existing:
                test_case = TestCase(**case_data)
                db.add(test_case)
        
        # 创建Agent任务示例测试用例
        agent_cases = [
            {
                "name": "数学计算任务",
                "task_type": "agent",
                "description": "测试Agent执行数学计算任务",
                "input_data": {
                    "task": "计算 (25 + 15) * 3 的结果",
                    "context": {},
                    "tools": ["calculator"]
                },
                "expected_output": {
                    "result": "计算结果是120。具体步骤：(25 + 15) * 3 = 40 * 3 = 120",
                    "actions_taken": [
                        {
                            "tool": "calculator",
                            "args": {"expression": "(25 + 15) * 3"},
                            "result": "(25 + 15) * 3 = 120",
                            "status": "success"
                        }
                    ],
                    "confidence": 0.95
                }
            },
            {
                "name": "文本分析任务",
                "task_type": "agent",
                "description": "测试Agent执行文本分析任务",
                "input_data": {
                    "task": "分析这段文本的基本信息：'人工智能技术正在快速发展，为各行各业带来了革命性的变化。'",
                    "context": {},
                    "tools": ["text_analyzer"]
                },
                "expected_output": {
                    "result": "这段文本包含32个字符，描述了人工智能技术的发展及其影响。文本表达了积极的观点。",
                    "actions_taken": [
                        {
                            "tool": "text_analyzer",
                            "args": {"text": "人工智能技术正在快速发展，为各行各业带来了革命性的变化。"},
                            "result": "文本分析结果：字符数 32，单词数 1",
                            "status": "success"
                        }
                    ],
                    "confidence": 0.8
                }
            }
        ]
        
        for case_data in agent_cases:
            existing = db.query(TestCase).filter(TestCase.name == case_data["name"]).first()
            if not existing:
                test_case = TestCase(**case_data)
                db.add(test_case)
        
        # 创建测试套件
        test_suites = [
            {
                "name": "基础分类测试套件",
                "description": "包含基本的分类任务测试用例",
                "task_type": "classification",
                "test_case_ids": [1, 2, 3]  # 假设这些是分类测试用例的ID
            },
            {
                "name": "综合测试套件",
                "description": "包含各种类型的测试用例",
                "task_type": "mixed",
                "test_case_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        ]
        
        for suite_data in test_suites:
            existing = db.query(TestSuite).filter(TestSuite.name == suite_data["name"]).first()
            if not existing:
                test_suite = TestSuite(**suite_data)
                db.add(test_suite)
        
        # 提交所有更改
        db.commit()
        print("✅ 示例数据创建成功！")
        
        # 显示统计信息
        test_case_count = db.query(TestCase).count()
        model_count = db.query(Model).count()
        suite_count = db.query(TestSuite).count()
        
        print(f"📊 数据统计:")
        print(f"   - 测试用例: {test_case_count}")
        print(f"   - 模型配置: {model_count}")
        print(f"   - 测试套件: {suite_count}")
        
    except Exception as e:
        print(f"❌ 创建示例数据失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()