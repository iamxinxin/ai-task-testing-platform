from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import time

from app.database import get_db
from app.models.test_models import TestCase, TestResult
from app.schemas.test_schemas import (
    TestCase as TestCaseSchema,
    TestCaseCreate,
    DialogueInput,
    DialogueOutput
)
from app.services.dialogue_service import DialogueService

router = APIRouter()

@router.post("/test-cases/", response_model=TestCaseSchema)
async def create_dialogue_test_case(
    test_case: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """创建对话任务测试用例"""
    if test_case.task_type != "dialogue":
        raise HTTPException(status_code=400, detail="任务类型必须是 'dialogue'")
    
    db_test_case = TestCase(**test_case.dict())
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

@router.get("/test-cases/", response_model=List[TestCaseSchema])
async def get_dialogue_test_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取对话任务测试用例列表"""
    test_cases = db.query(TestCase).filter(
        TestCase.task_type == "dialogue",
        TestCase.is_active == True
    ).offset(skip).limit(limit).all()
    return test_cases

@router.post("/test-cases/{test_case_id}/run")
async def run_dialogue_test(
    test_case_id: int,
    request_data: dict,
    db: Session = Depends(get_db)
):
    """运行对话任务测试"""
    model_name = request_data.get("model_name")
    temperature = request_data.get("temperature", 0.7)
    max_tokens = request_data.get("max_tokens", 150)
    
    if not model_name:
        raise HTTPException(status_code=400, detail="缺少model_name参数")
        
    return await _run_dialogue_test_internal(test_case_id, model_name, temperature, max_tokens, db)

@router.post("/run-test/")
async def run_dialogue_test_form(
    test_case_id: int,
    model_name: str,
    db: Session = Depends(get_db)
):
    """运行对话任务测试（表单方式）"""
    return await _run_dialogue_test_internal(test_case_id, model_name, 0.7, 150, db)

async def _run_dialogue_test_internal(
    test_case_id: int,
    model_name: str,
    temperature: float,
    max_tokens: int,
    db: Session
):
    """运行对话任务测试"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    if test_case.task_type != "dialogue":
        raise HTTPException(status_code=400, detail="测试用例类型不匹配")
    
    try:
        start_time = time.time()
        
        dialogue_service = DialogueService()
        
        # 适配我们的数据结构
        input_data = DialogueInput(
            message=test_case.input_data.get("user_input"),
            context=test_case.input_data.get("conversation_history"),
            user_id=test_case.input_data.get("user_id")
        )
        
        result = await dialogue_service.generate_response(
            message=input_data.message,
            model_name=model_name,
            context=input_data.context,
            user_id=input_data.user_id
        )
        
        execution_time = time.time() - start_time
        
        # 适配expected_output结构
        expected_output = DialogueOutput(
            response="",  # 这里不需要具体的响应文本
            confidence=0.8,  # 默认置信度
            context_used=True
        )
        metrics = dialogue_service.evaluate(result, expected_output)
        
        test_result = TestResult(
            test_case_id=test_case_id,
            model_name=model_name,
            actual_output=result.dict(),
            score=metrics.get("relevance_score", 0.0),
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
async def run_batch_dialogue_test(
    test_case_ids: List[int],
    model_names: List[str],
    db: Session = Depends(get_db)
):
    """批量运行对话任务测试"""
    results = []
    
    for test_case_id in test_case_ids:
        for model_name in model_names:
            try:
                result = await run_dialogue_test(test_case_id, model_name, db)
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

@router.post("/interactive-test/")
async def interactive_dialogue_test(
    model_name: str,
    message: str,
    context: List[dict] = None,
    user_id: str = None
):
    """交互式对话测试"""
    dialogue_service = DialogueService()
    
    try:
        result = await dialogue_service.generate_response(
            message=message,
            model_name=model_name,
            context=context,
            user_id=user_id
        )
        
        return {
            "response": result.response,
            "confidence": result.confidence,
            "context_used": result.context_used
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对话生成失败: {str(e)}")