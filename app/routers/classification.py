from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import time
import json

from app.database import get_db
from app.models.test_models import TestCase, TestResult
from app.schemas.test_schemas import (
    TestCase as TestCaseSchema,
    TestCaseCreate,
    TestResult as TestResultSchema,
    ClassificationInput,
    ClassificationOutput
)
from app.services.classification_service import ClassificationService

router = APIRouter()

@router.post("/test-cases/", response_model=TestCaseSchema)
async def create_classification_test_case(
    test_case: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """创建分类任务测试用例"""
    if test_case.task_type != "classification":
        raise HTTPException(
            status_code=400,
            detail="任务类型必须是 'classification'"
        )
    
    db_test_case = TestCase(**test_case.dict())
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

@router.get("/test-cases/", response_model=List[TestCaseSchema])
async def get_classification_test_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取分类任务测试用例列表"""
    test_cases = db.query(TestCase).filter(
        TestCase.task_type == "classification",
        TestCase.is_active == True
    ).offset(skip).limit(limit).all()
    return test_cases

@router.post("/run-test/")
async def run_classification_test(
    test_case_id: int = Form(...),
    model_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """运行分类任务测试"""
    # 获取测试用例
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    if test_case.task_type != "classification":
        raise HTTPException(status_code=400, detail="测试用例类型不匹配")
    
    try:
        start_time = time.time()
        
        # 初始化分类服务
        classification_service = ClassificationService()
        
        # 解析输入数据
        input_data = ClassificationInput(**test_case.input_data)
        
        # 运行分类任务
        result = await classification_service.classify(
            text=input_data.text,
            model_name=model_name,
            labels=input_data.labels
        )
        
        execution_time = time.time() - start_time
        
        # 计算评估指标
        expected_output = ClassificationOutput(**test_case.expected_output)
        metrics = classification_service.evaluate(result, expected_output)
        
        # 保存测试结果
        test_result = TestResult(
            test_case_id=test_case_id,
            model_name=model_name,
            actual_output=result.dict(),
            score=metrics.get("accuracy", 0.0),
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
        # 保存错误结果
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
async def run_batch_classification_test(
    test_case_ids: List[int],
    model_names: List[str],
    db: Session = Depends(get_db)
):
    """批量运行分类任务测试"""
    results = []
    
    for test_case_id in test_case_ids:
        for model_name in model_names:
            try:
                result = await run_classification_test(test_case_id, model_name, db)
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

@router.get("/results/{test_case_id}")
async def get_classification_results(
    test_case_id: int,
    db: Session = Depends(get_db)
):
    """获取分类任务测试结果"""
    results = db.query(TestResult).filter(
        TestResult.test_case_id == test_case_id
    ).all()
    
    return {"test_case_id": test_case_id, "results": results}

@router.get("/models/performance")
async def get_model_performance(
    task_type: str = "classification",
    db: Session = Depends(get_db)
):
    """获取模型性能对比"""
    # 查询所有分类任务的测试结果
    results = db.query(TestResult).join(TestCase).filter(
        TestCase.task_type == task_type,
        TestResult.status == "completed"
    ).all()
    
    # 按模型聚合性能数据
    model_performance = {}
    for result in results:
        model_name = result.model_name
        if model_name not in model_performance:
            model_performance[model_name] = {
                "total_tests": 0,
                "avg_score": 0,
                "avg_execution_time": 0,
                "scores": []
            }
        
        model_performance[model_name]["total_tests"] += 1
        model_performance[model_name]["scores"].append(result.score or 0)
        model_performance[model_name]["avg_execution_time"] += result.execution_time or 0
    
    # 计算平均值
    for model_name, data in model_performance.items():
        if data["total_tests"] > 0:
            data["avg_score"] = sum(data["scores"]) / len(data["scores"])
            data["avg_execution_time"] /= data["total_tests"]
    
    return model_performance