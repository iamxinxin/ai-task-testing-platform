from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
import time

from app.database import get_db
from app.models.test_models import TestCase, TestResult
from app.schemas.test_schemas import (
    TestCase as TestCaseSchema,
    TestCaseCreate,
    AgentInput,
    AgentOutput
)
from app.services.agent_service import AgentService

router = APIRouter()

@router.post("/test-cases/", response_model=TestCaseSchema)
async def create_agent_test_case(
    test_case: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """创建Agent任务测试用例"""
    if test_case.task_type != "agent":
        raise HTTPException(status_code=400, detail="任务类型必须是 'agent'")
    
    db_test_case = TestCase(**test_case.dict())
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

@router.get("/test-cases/", response_model=List[TestCaseSchema])
async def get_agent_test_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取Agent任务测试用例列表"""
    test_cases = db.query(TestCase).filter(
        TestCase.task_type == "agent",
        TestCase.is_active == True
    ).offset(skip).limit(limit).all()
    return test_cases

@router.post("/test-cases/{test_case_id}/run")
async def run_agent_test(
    test_case_id: int,
    request_data: dict,
    db: Session = Depends(get_db)
):
    """运行Agent任务测试"""
    model_name = request_data.get("model_name")
    execution_mode = request_data.get("execution_mode", "autonomous")
    timeout = request_data.get("timeout", 300)
    verbose_logging = request_data.get("verbose_logging", False)
    
    if not model_name:
        raise HTTPException(status_code=400, detail="缺少model_name参数")
        
    return await _run_agent_test_internal(test_case_id, model_name, execution_mode, timeout, verbose_logging, db)

@router.post("/run-test/")
async def run_agent_test_form(
    test_case_id: int = Form(...),
    model_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """运行Agent任务测试（表单方式）"""
    return await _run_agent_test_internal(test_case_id, model_name, "autonomous", 300, False, db)

async def _run_agent_test_internal(
    test_case_id: int,
    model_name: str,
    execution_mode: str,
    timeout: int,
    verbose_logging: bool,
    db: Session
):
    """运行Agent任务测试"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    if test_case.task_type != "agent":
        raise HTTPException(status_code=400, detail="测试用例类型不匹配")
    
    try:
        start_time = time.time()
        
        agent_service = AgentService()
        
        # 适配我们的数据结构
        input_data = AgentInput(
            task=test_case.input_data.get("task_goal"),
            context={"initial_state": test_case.input_data.get("initial_state")},
            tools=[tool.get("name") for tool in test_case.input_data.get("available_tools", [])]
        )
        
        result = await agent_service.execute_task(
            task=input_data.task,
            model_name=model_name,
            context=input_data.context,
            tools=input_data.tools
        )
        
        execution_time = time.time() - start_time
        
        # 适配expected_output结构
        expected_output = AgentOutput(
            result=test_case.expected_output.get("expected_result", ""),
            actions_taken=[],  # 空的动作列表
            confidence=0.8  # 默认置信度
        )
        metrics = agent_service.evaluate(result, expected_output)
        
        test_result = TestResult(
            test_case_id=test_case_id,
            model_name=model_name,
            actual_output=result.dict(),
            score=metrics.get("task_completion_score", 0.0),
            metrics=metrics,
            execution_time=execution_time,
            status="completed"
        )
        
        db.add(test_result)
        db.commit()
        db.refresh(test_result)
        
        return {
            "test_result_id": test_result.id,
            "result": result,
            "metrics": metrics,
            "execution_time": execution_time
        }
        
    except Exception as e:
        test_result = TestResult(
            test_case_id=test_case_id,
            model_name=model_name,
            actual_output={},
            status="failed",
            error_message=str(e),
            execution_time=time.time() - start_time
        )
        
        db.add(test_result)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"测试执行失败: {str(e)}")

@router.post("/batch-test/")
async def run_batch_agent_test(
    test_case_ids: List[int],
    model_names: List[str],
    db: Session = Depends(get_db)
):
    """批量运行Agent任务测试"""
    results = []
    
    for test_case_id in test_case_ids:
        for model_name in model_names:
            try:
                result = await run_agent_test(test_case_id, model_name, db)
                results.append({
                    "test_case_id": test_case_id,
                    "model_name": model_name,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results.append({
                    "test_case_id": test_case_id,
                    "model_name": model_name,
                    "status": "failed",
                    "error": str(e)
                })
    
    return {"batch_results": results}

@router.get("/available-tools/")
async def get_available_tools():
    """获取可用的工具列表"""
    agent_service = AgentService()
    return {"tools": agent_service.get_available_tools()}

@router.post("/interactive-test/")
async def interactive_agent_test(
    task: str,
    model_name: str,
    context: dict = None,
    tools: List[str] = None
):
    """交互式Agent测试"""
    agent_service = AgentService()
    
    try:
        result = await agent_service.execute_task(
            task=task,
            model_name=model_name,
            context=context,
            tools=tools
        )
        
        return {
            "result": result.result,
            "actions_taken": result.actions_taken,
            "confidence": result.confidence
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent任务执行失败: {str(e)}")