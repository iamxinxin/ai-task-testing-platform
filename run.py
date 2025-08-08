#!/usr/bin/env python3
"""
AI任务自动化测试平台启动脚本
"""

import uvicorn
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

if __name__ == "__main__":
    # 获取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 12000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🚀 启动AI任务自动化测试平台")
    print(f"📍 地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    
    # 启动服务器
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=debug,
        access_log=True,
        log_level="info" if not debug else "debug"
    )