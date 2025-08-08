from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import time

from app.database import get_db
from app.models.test_models import TestCase, TestResult
from app.schemas.test_schemas import (
    TestCase as TestCaseSchema,
    TestCaseCreate,
    RAGInput,
    RAGOutput
)
from app.services.rag_service import RAGService

router = APIRouter()

@router.post("/test-cases/", response_model=TestCaseSchema)
async def create_rag_test_case(
    test_case: TestCaseCreate,
    db: Session = Depends(get_db)
):
    """创建RAG任务测试用例"""
    if test_case.task_type != "rag":
        raise HTTPException(status_code=400, detail="任务类型必须是 'rag'")
    
    db_test_case = TestCase(**test_case.dict())
    db.add(db_test_case)
    db.commit()
    db.refresh(db_test_case)
    return db_test_case

@router.get("/test-cases/", response_model=List[TestCaseSchema])
async def get_rag_test_cases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取RAG任务测试用例列表"""
    test_cases = db.query(TestCase).filter(
        TestCase.task_type == "rag",
        TestCase.is_active == True
    ).offset(skip).limit(limit).all()
    return test_cases

@router.post("/run-test/")
async def run_rag_test(
    test_case_id: int,
    model_name: str,
    db: Session = Depends(get_db)
):
    """运行RAG任务测试"""
    test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="测试用例不存在")
    
    if test_case.task_type != "rag":
        raise HTTPException(status_code=400, detail="测试用例类型不匹配")
    
    try:
        start_time = time.time()
        
        rag_service = RAGService()
        input_data = RAGInput(**test_case.input_data)
        
        result = await rag_service.generate_answer(
            query=input_data.query,
            model_name=model_name,
            documents=input_data.documents,
            top_k=input_data.top_k
        )
        
        execution_time = time.time() - start_time
        
        expected_output = RAGOutput(**test_case.expected_output)
        metrics = rag_service.evaluate(result, expected_output)
        
        test_result = TestResult(
            test_case_id=test_case_id,
            model_name=model_name,
            actual_output=result.dict(),
            score=metrics.get("answer_quality", 0.0),
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
async def run_batch_rag_test(
    test_case_ids: List[int],
    model_names: List[str],
    db: Session = Depends(get_db)
):
    """批量运行RAG任务测试"""
    results = []
    
    for test_case_id in test_case_ids:
        for model_name in model_names:
            try:
                result = await run_rag_test(test_case_id, model_name, db)
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

@router.post("/upload-documents/")
async def upload_documents(
    documents: List[str],
    collection_name: str = "default"
):
    """上传文档到向量数据库"""
    rag_service = RAGService()
    
    try:
        result = await rag_service.add_documents(documents, collection_name)
        return {
            "message": f"成功上传 {len(documents)} 个文档",
            "collection_name": collection_name,
            "document_ids": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")

@router.post("/search-documents/")
async def search_documents(
    query: str,
    collection_name: str = "default",
    top_k: int = 5
):
    """搜索相关文档"""
    rag_service = RAGService()
    
    try:
        results = await rag_service.search_documents(query, collection_name, top_k)
        return {
            "query": query,
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档搜索失败: {str(e)}")