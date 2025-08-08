from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base

class TestCase(Base):
    """测试用例基础模型"""
    __tablename__ = "test_cases"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    task_type = Column(String(50), nullable=False)  # classification, correction, dialogue, rag, agent
    description = Column(Text)
    input_data = Column(JSON)
    expected_output = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class TestResult(Base):
    """测试结果模型"""
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_case_id = Column(Integer, nullable=False)
    model_name = Column(String(255), nullable=False)
    actual_output = Column(JSON)
    score = Column(Float)
    metrics = Column(JSON)  # 存储各种评估指标
    execution_time = Column(Float)  # 执行时间（秒）
    status = Column(String(50), default="completed")  # completed, failed, running
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TestSuite(Base):
    """测试套件模型"""
    __tablename__ = "test_suites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    task_type = Column(String(50), nullable=False)
    test_case_ids = Column(JSON)  # 包含的测试用例ID列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

class Model(Base):
    """模型配置"""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    model_type = Column(String(50), nullable=False)  # openai, anthropic, huggingface, local
    config = Column(JSON)  # 模型配置参数
    api_endpoint = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())