# AI任务自动化测试平台

一个功能完整的AI任务自动化测试平台，支持分类、纠错、对话、RAG、Agent等多种AI任务的测试和评估。

## 🚀 功能特性

### 支持的任务类型
- **分类任务**: 文本分类、情感分析等
- **纠错任务**: 语法纠错、拼写检查、风格改进
- **对话任务**: 聊天机器人、问答系统
- **RAG任务**: 检索增强生成系统
- **Agent任务**: 智能代理系统

### 核心功能
- 📝 **测试用例管理**: 创建、编辑、删除测试用例
- 🤖 **多模型支持**: OpenAI GPT、Anthropic Claude、HuggingFace等
- 📊 **性能评估**: 多维度指标评估和对比
- 📈 **可视化仪表板**: 实时监控测试结果和性能趋势
- 🔄 **批量测试**: 支持批量运行测试用例
- 📋 **测试套件**: 组织和管理相关测试用例
- 📤 **结果导出**: 支持测试结果导出和分析

## 🛠️ 技术栈

### 后端
- **FastAPI**: 现代、快速的Web框架
- **SQLAlchemy**: ORM数据库操作
- **Pydantic**: 数据验证和序列化
- **SQLite**: 轻量级数据库（可扩展到PostgreSQL/MySQL）

### 前端
- **Bootstrap 5**: 响应式UI框架
- **Chart.js**: 数据可视化
- **Vanilla JavaScript**: 原生JS实现

### AI集成
- **OpenAI API**: GPT系列模型
- **Anthropic API**: Claude系列模型
- **HuggingFace**: 开源模型支持
- **Sentence Transformers**: 文本嵌入

## 📦 安装和部署

### 1. 环境要求
- Python 3.8+
- pip 或 poetry

### 2. 克隆项目
```bash
git clone <repository-url>
cd ai-test-platform
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 环境配置
复制环境变量模板并配置：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置API密钥：
```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database
DATABASE_URL=sqlite:///./test_platform.db

# Server
HOST=0.0.0.0
PORT=12000
DEBUG=True
```

### 5. 初始化数据库和示例数据
```bash
python init_data.py
```

### 6. 启动服务
```bash
python run.py
```

访问 http://localhost:12000 查看平台界面。

## 📖 使用指南

### 创建测试用例

#### 分类任务测试用例
```python
{
    "name": "情感分析测试",
    "task_type": "classification",
    "description": "测试情感分析准确性",
    "input_data": {
        "text": "这个产品真的很棒！",
        "labels": ["positive", "negative", "neutral"]
    },
    "expected_output": {
        "predicted_label": "positive",
        "confidence": 0.9
    }
}
```

#### 纠错任务测试用例
```python
{
    "name": "语法纠错测试",
    "task_type": "correction",
    "description": "测试语法错误纠正",
    "input_data": {
        "text": "I have went to store.",
        "correction_type": "grammar"
    },
    "expected_output": {
        "corrected_text": "I went to the store.",
        "corrections": [...],
        "confidence": 0.9
    }
}
```

### API使用示例

#### 运行分类测试
```bash
curl -X POST "http://localhost:12000/api/classification/run-test/" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "test_case_id=1&model_name=gpt-3.5-turbo"
```

#### 获取测试结果
```bash
curl "http://localhost:12000/api/classification/results/1"
```

#### 批量测试
```bash
curl -X POST "http://localhost:12000/api/classification/batch-test/" \
     -H "Content-Type: application/json" \
     -d '{
       "test_case_ids": [1, 2, 3],
       "model_names": ["gpt-3.5-turbo", "claude-3-sonnet"]
     }'
```

## 📊 评估指标

### 分类任务
- **准确率**: 预测标签与期望标签的匹配度
- **置信度差异**: 预测置信度与期望置信度的差异
- **执行时间**: 模型响应时间

### 纠错任务
- **文本相似度**: 纠错结果与期望结果的相似度
- **纠错数量**: 识别和修正的错误数量
- **置信度评估**: 纠错置信度评估

### 对话任务
- **相关性评分**: 回答与问题的相关程度
- **长度合理性**: 回答长度是否合适
- **上下文使用**: 是否正确使用对话上下文

### RAG任务
- **答案质量**: 生成答案的准确性和完整性
- **检索质量**: 检索文档的相关性
- **置信度评估**: 答案的可信度

### Agent任务
- **任务完成度**: 任务执行的完整性
- **工具使用**: 工具选择和使用的合理性
- **执行效率**: 完成任务的步骤数和时间

## 🔧 扩展开发

### 添加新的任务类型

1. **创建数据模式**
```python
# app/schemas/test_schemas.py
class NewTaskInput(BaseModel):
    # 定义输入数据结构
    pass

class NewTaskOutput(BaseModel):
    # 定义输出数据结构
    pass
```

2. **实现服务类**
```python
# app/services/new_task_service.py
class NewTaskService:
    async def execute_task(self, input_data, model_name):
        # 实现任务执行逻辑
        pass
    
    def evaluate(self, predicted, expected):
        # 实现评估逻辑
        pass
```

3. **创建路由**
```python
# app/routers/new_task.py
router = APIRouter()

@router.post("/run-test/")
async def run_new_task_test():
    # 实现测试运行逻辑
    pass
```

### 添加新的模型支持

1. **在服务类中添加模型支持**
```python
async def _execute_new_model(self, input_data, model_name):
    # 实现新模型的调用逻辑
    pass
```

2. **更新模型配置**
```python
# 在数据库中添加新模型配置
new_model = Model(
    name="new-model",
    model_type="new_provider",
    config={"param1": "value1"},
    api_endpoint="https://api.newprovider.com"
)
```

## 📈 监控和分析

### 仪表板功能
- **实时概览**: 测试数量、平均分数、执行时间等关键指标
- **性能对比**: 不同模型在各任务上的性能对比
- **趋势分析**: 测试结果随时间的变化趋势
- **错误分析**: 失败测试的错误类型和原因分析

### 数据导出
支持将测试结果导出为JSON格式，便于进一步分析：
```bash
curl "http://localhost:12000/api/dashboard/export-results?task_type=classification&start_date=2024-01-01"
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持和反馈

如果您在使用过程中遇到问题或有改进建议，请：

1. 查看 [Issues](../../issues) 页面
2. 创建新的 Issue 描述问题
3. 联系开发团队

## 🔮 未来规划

- [ ] 支持更多AI模型和API
- [ ] 增加更多评估指标
- [ ] 实现分布式测试执行
- [ ] 添加测试结果可视化分析
- [ ] 支持自定义评估函数
- [ ] 集成CI/CD流水线
- [ ] 添加用户权限管理
- [ ] 支持测试用例版本控制

---

**AI任务自动化测试平台** - 让AI模型测试更简单、更高效！