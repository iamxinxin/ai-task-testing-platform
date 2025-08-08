from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class TestCaseBase(BaseModel):
    name: str = Field(..., description="测试用例名称")
    task_type: str = Field(..., description="任务类型")
    description: Optional[str] = Field(None, description="测试用例描述")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    expected_output: Dict[str, Any] = Field(..., description="期望输出")

class TestCaseCreate(TestCaseBase):
    pass

class TestCaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    expected_output: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class TestCase(TestCaseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

class TestResultBase(BaseModel):
    test_case_id: int
    model_name: str
    actual_output: Dict[str, Any]
    score: Optional[float] = None
    metrics: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    status: str = "completed"
    error_message: Optional[str] = None

class TestResultCreate(TestResultBase):
    pass

class TestResult(TestResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TestSuiteBase(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: str
    test_case_ids: List[int]

class TestSuiteCreate(TestSuiteBase):
    pass

class TestSuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    test_case_ids: Optional[List[int]] = None
    is_active: Optional[bool] = None

class TestSuite(TestSuiteBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

class ModelBase(BaseModel):
    name: str
    model_type: str
    config: Dict[str, Any]
    api_endpoint: Optional[str] = None

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    name: Optional[str] = None
    model_type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    api_endpoint: Optional[str] = None
    is_active: Optional[bool] = None

class Model(ModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

# 任务特定的模式
class ClassificationInput(BaseModel):
    text: str
    labels: Optional[List[str]] = None

class ClassificationOutput(BaseModel):
    predicted_label: str
    confidence: float
    probabilities: Optional[Dict[str, float]] = None

class CorrectionInput(BaseModel):
    text: str
    correction_type: str = "grammar"  # grammar, spelling, style

class CorrectionOutput(BaseModel):
    corrected_text: str
    corrections: List[Dict[str, Any]]
    confidence: float

class DialogueInput(BaseModel):
    message: str
    context: Optional[List[Dict[str, str]]] = None
    user_id: Optional[str] = None

class DialogueOutput(BaseModel):
    response: str
    confidence: float
    context_used: Optional[bool] = None

class RAGInput(BaseModel):
    query: str
    documents: Optional[List[str]] = None
    top_k: int = 5

class RAGOutput(BaseModel):
    answer: str
    retrieved_documents: List[Dict[str, Any]]
    confidence: float

class AgentInput(BaseModel):
    task: str
    context: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None

class AgentOutput(BaseModel):
    result: str
    actions_taken: List[Dict[str, Any]]
    confidence: float