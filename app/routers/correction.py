from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List
import time

from app.database import get_db
from app.models.test_models import TestCase, TestResult
from app.schemas.test_schemas import (
    TestCase as TestCaseSchema,
    TestCaseCreate,
    CorrectionInput,
    CorrectionOutput
)
from app.services.correction_service import CorrectionService

router = APIRouter()

@router.post("/test-cases/", response_model=TestCaseSchema)
async def create_correction_test_case(
    test_case: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """创建纠错任务测试用例"""
    if test_case.task_type != "correction":
        raise HTTPException(status_code=400, detail="任务类型必须是 'correction'")
    
    db_test_case = TestCase(**test_case.dict())
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

@router.get("/test-cases/", response_model=List[TestCaseSchema])
async def get_correction_test_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取纠错任务测试用例列表"""
    test_cases = db.query(TestCase).filter(
        TestCase.task_type == "correction",
        TestCase.is_active == True
    ).offset(skip).limit(limit).all()
    return test_cases

@router.post("/run-test/")
async def run_correction_test(
    test_case_id: int = Form(...),
    model_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """运行纠错任务测试"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    if test_case.task_type != "correction":
        raise HTTPException(status_code=400, detail="测试用例类型不匹配")
    
    try:
        start_time = time.time()
        
        correction_service = CorrectionService()
        input_data = CorrectionInput(**test_case.input_data)
        
        result = await correction_service.correct(
            text=input_data.text,
            model_name=model_name,
            correction_type=input_data.correction_type
        )
        
        execution_time = time.time() - start_time
        
        expected_output = CorrectionOutput(**test_case.expected_output)
        metrics = correction_service.evaluate(result, expected_output)
        
        test_result = TestResult(
            test_case_id=test_case_id,
            model_name=model_name,
            actual_output=result.dict(),
            score=metrics.get("similarity_score", 0.0),
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
async def run_batch_correction_test(
    test_case_ids: List[int],
    model_names: List[str],
    db: Session = Depends(get_db)
):
    """批量运行纠错任务测试"""
    results = []
    
    for test_case_id in test_case_ids:
        for model_name in model_names:
            try:
                result = await run_correction_test(test_case_id, model_name, db)
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