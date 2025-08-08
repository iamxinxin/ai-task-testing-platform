from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
import json
from datetime import datetime, timedelta

from app.database import get_db
from app.models.test_models import TestCase, TestResult, TestSuite

router = APIRouter()

@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """获取仪表板概览数据"""
    
    # 统计各类任务的测试用例数量
    task_stats = db.query(
        TestCase.task_type,
        func.count(TestCase.id).label('count')
    ).filter(TestCase.is_active == True).group_by(TestCase.task_type).all()
    
    # 统计测试结果
    result_stats = db.query(
        TestResult.status,
        func.count(TestResult.id).label('count')
    ).group_by(TestResult.status).all()
    
    # 最近7天的测试活动
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_tests = db.query(func.count(TestResult.id)).filter(
        TestResult.created_at >= seven_days_ago
    ).scalar()
    
    # 平均执行时间
    avg_execution_time = db.query(func.avg(TestResult.execution_time)).filter(
        TestResult.execution_time.isnot(None)
    ).scalar()
    
    # 平均分数
    avg_score = db.query(func.avg(TestResult.score)).filter(
        TestResult.score.isnot(None)
    ).scalar()
    
    return {
        "task_statistics": {item.task_type: item.count for item in task_stats},
        "result_statistics": {item.status: item.count for item in result_stats},
        "recent_tests_count": recent_tests or 0,
        "average_execution_time": float(avg_execution_time) if avg_execution_time else 0.0,
        "average_score": float(avg_score) if avg_score else 0.0
    }

@router.get("/model-performance")
async def get_model_performance(
    task_type: str = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取模型性能对比"""
    
    query = db.query(
        TestResult.model_name,
        func.count(TestResult.id).label('total_tests'),
        func.avg(TestResult.score).label('avg_score'),
        func.avg(TestResult.execution_time).label('avg_execution_time'),
        func.count(func.nullif(TestResult.status == 'completed', False)).label('success_count')
    ).filter(TestResult.score.isnot(None))
    
    if task_type:
        query = query.join(TestCase).filter(TestCase.task_type == task_type)
    
    results = query.group_by(TestResult.model_name).order_by(
        desc('avg_score')
    ).limit(limit).all()
    
    performance_data = []
    for result in results:
        success_rate = (result.success_count / result.total_tests) if result.total_tests > 0 else 0
        performance_data.append({
            "model_name": result.model_name,
            "total_tests": result.total_tests,
            "average_score": float(result.avg_score) if result.avg_score else 0.0,
            "average_execution_time": float(result.avg_execution_time) if result.avg_execution_time else 0.0,
            "success_rate": success_rate
        })
    
    return {"model_performance": performance_data}

@router.get("/task-performance/{task_type}")
async def get_task_performance(
    task_type: str,
    db: Session = Depends(get_db)
):
    """获取特定任务类型的性能数据"""
    
    # 获取该任务类型的所有测试结果
    results = db.query(TestResult).join(TestCase).filter(
        TestCase.task_type == task_type,
        TestResult.status == 'completed'
    ).all()
    
    if not results:
        return {"message": f"没有找到 {task_type} 任务的测试结果"}
    
    # 按模型分组统计
    model_stats = {}
    for result in results:
        model_name = result.model_name
        if model_name not in model_stats:
            model_stats[model_name] = {
                "scores": [],
                "execution_times": [],
                "test_count": 0
            }
        
        model_stats[model_name]["test_count"] += 1
        if result.score is not None:
            model_stats[model_name]["scores"].append(result.score)
        if result.execution_time is not None:
            model_stats[model_name]["execution_times"].append(result.execution_time)
    
    # 计算统计指标
    performance_summary = {}
    for model_name, stats in model_stats.items():
        scores = stats["scores"]
        times = stats["execution_times"]
        
        performance_summary[model_name] = {
            "test_count": stats["test_count"],
            "avg_score": sum(scores) / len(scores) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "avg_execution_time": sum(times) / len(times) if times else 0,
            "min_execution_time": min(times) if times else 0,
            "max_execution_time": max(times) if times else 0
        }
    
    return {
        "task_type": task_type,
        "performance_summary": performance_summary
    }

@router.get("/recent-tests")
async def get_recent_tests(
    limit: int = 20,
    task_type: str = None,
    db: Session = Depends(get_db)
):
    """获取最近的测试结果"""
    
    query = db.query(TestResult)
    
    if task_type:
        # 只有在需要过滤任务类型时才进行JOIN
        query = query.join(TestCase).filter(TestCase.task_type == task_type)
    
    recent_tests = query.order_by(desc(TestResult.created_at)).limit(limit).all()
    
    test_data = []
    for test in recent_tests:
        test_case = db.query(TestCase).filter(TestCase.id == test.test_case_id).first()
        test_data.append({
            "test_result_id": test.id,
            "test_case_id": test.test_case_id,
            "test_case_name": test_case.name if test_case else "Unknown",
            "task_type": test_case.task_type if test_case else "Unknown",
            "model_name": test.model_name,
            "score": test.score,
            "status": test.status,
            "execution_time": test.execution_time,
            "created_at": test.created_at
        })
    
    return {"recent_tests": test_data}

@router.get("/test-trends")
async def get_test_trends(
    days: int = 30,
    task_type: str = None,
    db: Session = Depends(get_db)
):
    """获取测试趋势数据"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(
        func.date(TestResult.created_at).label('test_date'),
        func.count(TestResult.id).label('test_count'),
        func.avg(TestResult.score).label('avg_score')
    ).filter(TestResult.created_at >= start_date)
    
    if task_type:
        query = query.join(TestCase).filter(TestCase.task_type == task_type)
    
    trends = query.group_by(func.date(TestResult.created_at)).order_by('test_date').all()
    
    trend_data = []
    for trend in trends:
        trend_data.append({
            "date": trend.test_date.isoformat(),
            "test_count": trend.test_count,
            "average_score": float(trend.avg_score) if trend.avg_score else 0.0
        })
    
    return {"trends": trend_data}

@router.get("/error-analysis")
async def get_error_analysis(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取错误分析数据"""
    
    # 获取失败的测试结果
    failed_tests = db.query(TestResult).filter(
        TestResult.status == 'failed',
        TestResult.error_message.isnot(None)
    ).order_by(desc(TestResult.created_at)).limit(limit * 2).all()
    
    # 分析错误类型
    error_types = {}
    error_details = []
    
    for test in failed_tests:
        error_msg = test.error_message
        
        # 简单的错误分类
        if "API" in error_msg or "api" in error_msg:
            error_type = "API错误"
        elif "timeout" in error_msg.lower():
            error_type = "超时错误"
        elif "key" in error_msg.lower():
            error_type = "认证错误"
        elif "json" in error_msg.lower() or "parse" in error_msg.lower():
            error_type = "解析错误"
        else:
            error_type = "其他错误"
        
        error_types[error_type] = error_types.get(error_type, 0) + 1
        
        if len(error_details) < limit:
            test_case = db.query(TestCase).filter(TestCase.id == test.test_case_id).first()
            error_details.append({
                "test_result_id": test.id,
                "test_case_name": test_case.name if test_case else "Unknown",
                "model_name": test.model_name,
                "error_type": error_type,
                "error_message": error_msg,
                "created_at": test.created_at
            })
    
    return {
        "error_types": error_types,
        "error_details": error_details
    }

@router.get("/test-suites")
async def get_test_suites(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取测试套件列表"""
    
    test_suites = db.query(TestSuite).filter(
        TestSuite.is_active == True
    ).offset(skip).limit(limit).all()
    
    suite_data = []
    for suite in test_suites:
        # 统计测试套件中的测试用例数量
        test_case_count = len(suite.test_case_ids) if suite.test_case_ids else 0
        
        suite_data.append({
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "task_type": suite.task_type,
            "test_case_count": test_case_count,
            "created_at": suite.created_at,
            "updated_at": suite.updated_at
        })
    
    return {"test_suites": suite_data}

@router.post("/export-results")
async def export_test_results(
    task_type: str = None,
    model_name: str = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    """导出测试结果"""
    
    query = db.query(TestResult).join(TestCase)
    
    # 应用过滤条件
    if task_type:
        query = query.filter(TestCase.task_type == task_type)
    
    if model_name:
        query = query.filter(TestResult.model_name == model_name)
    
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        query = query.filter(TestResult.created_at >= start_dt)
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        query = query.filter(TestResult.created_at <= end_dt)
    
    results = query.order_by(desc(TestResult.created_at)).all()
    
    export_data = []
    for result in results:
        test_case = db.query(TestCase).filter(TestCase.id == result.test_case_id).first()
        
        export_data.append({
            "test_result_id": result.id,
            "test_case_id": result.test_case_id,
            "test_case_name": test_case.name if test_case else "Unknown",
            "task_type": test_case.task_type if test_case else "Unknown",
            "model_name": result.model_name,
            "score": result.score,
            "metrics": result.metrics,
            "execution_time": result.execution_time,
            "status": result.status,
            "error_message": result.error_message,
            "created_at": result.created_at.isoformat()
        })
    
    return {
        "export_data": export_data,
        "total_records": len(export_data),
        "filters_applied": {
            "task_type": task_type,
            "model_name": model_name,
            "start_date": start_date,
            "end_date": end_date
        }
    }