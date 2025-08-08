// 全局变量
let currentSection = 'dashboard';
let charts = {};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// 初始化应用
function initializeApp() {
    loadDashboardData();
    loadAllTestCases();
    setupEventListeners();
}

// 设置事件监听器
function setupEventListeners() {
    // 分类任务表单提交
    document.getElementById('classification-form').addEventListener('submit', handleClassificationFormSubmit);
    document.getElementById('run-classification-test').addEventListener('submit', handleRunClassificationTest);
    
    // 纠错任务表单提交
    document.getElementById('correction-form').addEventListener('submit', handleCorrectionFormSubmit);
    document.getElementById('run-correction-test').addEventListener('submit', handleRunCorrectionTest);
    
    // 对话任务表单提交
    document.getElementById('dialogue-form').addEventListener('submit', handleDialogueFormSubmit);
    document.getElementById('run-dialogue-test').addEventListener('submit', handleRunDialogueTest);
    
    // RAG任务表单提交
    document.getElementById('rag-form').addEventListener('submit', handleRagFormSubmit);
    document.getElementById('run-rag-test').addEventListener('submit', handleRunRagTest);
    
    // Agent任务表单提交
    document.getElementById('agent-form').addEventListener('submit', handleAgentFormSubmit);
    document.getElementById('run-agent-test').addEventListener('submit', handleRunAgentTest);
}

// 显示指定部分
function showSection(sectionName) {
    // 隐藏所有部分
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.style.display = 'none';
    });
    
    // 显示指定部分
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.style.display = 'block';
        targetSection.classList.add('fade-in');
    }
    
    // 更新导航状态
    const navLinks = document.querySelectorAll('.sidebar .nav-link');
    navLinks.forEach(link => {
        link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[onclick="showSection('${sectionName}')"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
    
    currentSection = sectionName;
    
    // 根据部分加载相应数据
    switch (sectionName) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'classification':
            loadClassificationTestCases();
            break;
    }
}

// 显示加载状态
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
}

// 隐藏加载状态
function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

// 加载仪表板数据
async function loadDashboardData() {
    try {
        showLoading();
        
        // 加载概览数据
        const overviewResponse = await fetch('/api/dashboard/overview');
        const overviewData = await overviewResponse.json();
        
        updateOverviewCards(overviewData);
        
        // 加载模型性能数据
        const performanceResponse = await fetch('/api/dashboard/model-performance');
        const performanceData = await performanceResponse.json();
        
        updateModelPerformanceChart(performanceData);
        
        // 加载最近测试结果
        const recentTestsResponse = await fetch('/api/dashboard/recent-tests?limit=10');
        const recentTestsData = await recentTestsResponse.json();
        
        updateRecentTestsTable(recentTestsData);
        
        // 更新任务类型图表
        updateTaskTypeChart(overviewData.task_statistics);
        
    } catch (error) {
        console.error('加载仪表板数据失败:', error);
        showAlert('加载仪表板数据失败', 'danger');
    } finally {
        hideLoading();
    }
}

// 更新概览卡片
function updateOverviewCards(data) {
    const totalTests = Object.values(data.result_statistics || {}).reduce((sum, count) => sum + count, 0);
    
    document.getElementById('total-tests').textContent = totalTests;
    document.getElementById('avg-score').textContent = data.average_score.toFixed(2);
    document.getElementById('avg-time').textContent = data.average_execution_time.toFixed(2) + 's';
    document.getElementById('recent-tests').textContent = data.recent_tests_count;
}

// 更新任务类型图表
function updateTaskTypeChart(taskStats) {
    const ctx = document.getElementById('taskTypeChart').getContext('2d');
    
    if (charts.taskType) {
        charts.taskType.destroy();
    }
    
    charts.taskType = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(taskStats || {}),
            datasets: [{
                data: Object.values(taskStats || {}),
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// 更新模型性能图表
function updateModelPerformanceChart(data) {
    const ctx = document.getElementById('modelPerformanceChart').getContext('2d');
    
    if (charts.modelPerformance) {
        charts.modelPerformance.destroy();
    }
    
    const modelData = data.model_performance || [];
    
    charts.modelPerformance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: modelData.map(item => item.model_name),
            datasets: [{
                label: '平均分数',
                data: modelData.map(item => item.average_score),
                backgroundColor: '#36A2EB',
                borderColor: '#36A2EB',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1
                }
            }
        }
    });
}

// 更新最近测试结果表格
function updateRecentTestsTable(data) {
    const tbody = document.querySelector('#recent-tests-table tbody');
    tbody.innerHTML = '';
    
    const tests = data.recent_tests || [];
    
    tests.forEach(test => {
        const row = document.createElement('tr');
        
        const statusClass = getStatusClass(test.status);
        const scoreDisplay = test.score !== null ? test.score.toFixed(3) : 'N/A';
        const timeDisplay = test.execution_time !== null ? test.execution_time.toFixed(2) + 's' : 'N/A';
        
        row.innerHTML = `
            <td>${test.test_case_name}</td>
            <td><span class="badge bg-secondary">${test.task_type}</span></td>
            <td>${test.model_name}</td>
            <td>${scoreDisplay}</td>
            <td><span class="badge ${statusClass}">${test.status}</span></td>
            <td>${timeDisplay}</td>
            <td>${formatDateTime(test.created_at)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// 获取状态样式类
function getStatusClass(status) {
    switch (status) {
        case 'completed':
            return 'bg-success';
        case 'failed':
            return 'bg-danger';
        case 'running':
            return 'bg-warning';
        default:
            return 'bg-secondary';
    }
}

// 格式化日期时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 加载分类测试用例
// 加载所有任务类型的测试用例
async function loadAllTestCases() {
    await loadTestCasesForTaskType('classification');
    await loadTestCasesForTaskType('correction');
    await loadTestCasesForTaskType('dialogue');
    await loadTestCasesForTaskType('rag');
    await loadTestCasesForTaskType('agent');
}

// 加载指定任务类型的测试用例
async function loadTestCasesForTaskType(taskType) {
    try {
        const response = await fetch(`/api/${taskType}/test-cases/`);
        const data = await response.json();
        
        // 找到对应任务类型的选择框
        const section = document.getElementById(`${taskType}-section`);
        if (section) {
            const select = section.querySelector('select[name="test_case_id"]');
            if (select) {
                select.innerHTML = '<option value="">请选择测试用例</option>';
                
                data.forEach(testCase => {
                    const option = document.createElement('option');
                    option.value = testCase.id;
                    option.textContent = testCase.name;
                    select.appendChild(option);
                });
            }
        }
        
    } catch (error) {
        console.error(`加载${taskType}测试用例失败:`, error);
    }
}

// 保持向后兼容
async function loadClassificationTestCases() {
    await loadTestCasesForTaskType('classification');
}

// 处理分类表单提交
async function handleClassificationFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const labels = formData.get('labels') ? formData.get('labels').split(',').map(s => s.trim()) : null;
    
    const testCaseData = {
        name: formData.get('name'),
        task_type: 'classification',
        description: formData.get('description'),
        input_data: {
            text: formData.get('text'),
            labels: labels
        },
        expected_output: {
            predicted_label: formData.get('expected_label'),
            confidence: parseFloat(formData.get('expected_confidence'))
        }
    };
    
    try {
        showLoading();
        
        const response = await fetch('/api/classification/test-cases/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testCaseData)
        });
        
        if (response.ok) {
            const result = await response.json();
            showAlert('测试用例创建成功', 'success');
            event.target.reset();
            loadClassificationTestCases(); // 重新加载测试用例列表
        } else {
            const error = await response.json();
            showAlert('创建测试用例失败: ' + (error.detail || '未知错误'), 'danger');
        }
        
    } catch (error) {
        console.error('创建测试用例失败:', error);
        showAlert('创建测试用例失败: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

// 处理运行分类测试
async function handleRunClassificationTest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const testCaseId = formData.get('test_case_id');
    const modelName = formData.get('model_name');
    
    if (!testCaseId || !modelName) {
        showAlert('请选择测试用例和模型', 'warning');
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch('/api/classification/run-test/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `test_case_id=${testCaseId}&model_name=${modelName}`
        });
        
        if (response.ok) {
            const result = await response.json();
            displayTestResult(result);
            showAlert('测试执行成功', 'success');
        } else {
            const error = await response.json();
            showAlert('测试执行失败: ' + (error.detail || '未知错误'), 'danger');
        }
        
    } catch (error) {
        console.error('运行测试失败:', error);
        showAlert('运行测试失败: ' + error.message, 'danger');
    } finally {
        hideLoading();
    }
}

// 显示测试结果
function displayTestResult(result) {
    const resultDiv = document.getElementById('classification-result');
    const contentDiv = document.getElementById('classification-result-content');
    
    const formattedResult = JSON.stringify(result, null, 2);
    contentDiv.textContent = formattedResult;
    
    resultDiv.style.display = 'block';
}

// 显示警告消息
function showAlert(message, type = 'info') {
    // 创建警告元素
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 添加到页面顶部
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // 自动消失
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// API 请求辅助函数
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// ==================== 纠错任务处理函数 ====================

// 处理纠错表单提交
async function handleCorrectionFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    
    const testCaseData = {
        name: formData.get('name'),
        description: formData.get('description'),
        task_type: 'correction',
        input_data: {
            original_text: formData.get('original_text'),
            error_type: formData.get('error_type')
        },
        expected_output: {
            corrected_text: formData.get('expected_corrected'),
            min_similarity: parseFloat(formData.get('min_similarity'))
        }
    };
    
    try {
        showLoading();
        const response = await fetch('/api/correction/test-cases/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testCaseData)
        });
        
        if (response.ok) {
            showAlert('纠错测试用例创建成功！', 'success');
            event.target.reset();
            await loadTestCasesForTaskType('correction');
        } else {
            const error = await response.json();
            showAlert('创建失败: ' + (error.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('创建纠错测试用例失败:', error);
        showAlert('创建失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// 运行纠错测试
async function handleRunCorrectionTest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const testCaseId = formData.get('test_case_id');
    const modelName = formData.get('model_name');
    const correctionMode = formData.get('correction_mode');
    
    if (!testCaseId || !modelName) {
        showAlert('请选择测试用例和模型', 'error');
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`/api/correction/test-cases/${testCaseId}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model_name: modelName,
                correction_mode: correctionMode
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            displayTestResult('correction', result);
            loadDashboardData(); // 刷新仪表板数据
        } else {
            const error = await response.json();
            showAlert('测试运行失败: ' + (error.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('运行纠错测试失败:', error);
        showAlert('测试运行失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ==================== 对话任务处理函数 ====================

// 处理对话表单提交
async function handleDialogueFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    let conversationHistory;
    
    try {
        conversationHistory = JSON.parse(formData.get('conversation_history'));
    } catch (error) {
        showAlert('对话历史JSON格式错误', 'error');
        return;
    }
    
    const testCaseData = {
        name: formData.get('name'),
        description: formData.get('description'),
        task_type: 'dialogue',
        input_data: {
            conversation_history: conversationHistory,
            user_input: formData.get('user_input'),
            dialogue_type: formData.get('dialogue_type')
        },
        expected_output: {
            expected_keywords: formData.get('expected_keywords') ? formData.get('expected_keywords').split(',').map(s => s.trim()) : [],
            min_response_length: parseInt(formData.get('min_response_length'))
        }
    };
    
    try {
        showLoading();
        const response = await fetch('/api/dialogue/test-cases/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testCaseData)
        });
        
        if (response.ok) {
            showAlert('对话测试用例创建成功！', 'success');
            event.target.reset();
            await loadTestCasesForTaskType('dialogue');
        } else {
            const error = await response.json();
            showAlert('创建失败: ' + (error.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('创建对话测试用例失败:', error);
        showAlert('创建失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// 运行对话测试
async function handleRunDialogueTest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const testCaseId = formData.get('test_case_id');
    const modelName = formData.get('model_name');
    const temperature = parseFloat(formData.get('temperature'));
    const maxTokens = parseInt(formData.get('max_tokens'));
    
    if (!testCaseId || !modelName) {
        showAlert('请选择测试用例和模型', 'error');
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`/api/dialogue/test-cases/${testCaseId}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model_name: modelName,
                temperature: temperature,
                max_tokens: maxTokens
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            displayTestResult('dialogue', result);
            loadDashboardData(); // 刷新仪表板数据
        } else {
            const error = await response.json();
            showAlert('测试运行失败: ' + (error.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('运行对话测试失败:', error);
        showAlert('测试运行失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ==================== RAG任务处理函数 ====================

// 处理RAG表单提交
async function handleRagFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const knowledgeBase = formData.get('knowledge_base').split('\n').filter(doc => doc.trim());
    
    const testCaseData = {
        name: formData.get('name'),
        description: formData.get('description'),
        task_type: 'rag',
        input_data: {
            knowledge_base: knowledgeBase,
            query: formData.get('query'),
            rag_type: formData.get('rag_type'),
            top_k: parseInt(formData.get('top_k'))
        },
        expected_output: {
            expected_keywords: formData.get('expected_keywords') ? formData.get('expected_keywords').split(',').map(s => s.trim()) : [],
            min_relevance: parseFloat(formData.get('min_relevance'))
        }
    };
    
    try {
        showLoading();
        const response = await fetch('/api/rag/test-cases/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testCaseData)
        });
        
        if (response.ok) {
            showAlert('RAG测试用例创建成功！', 'success');
            event.target.reset();
            await loadTestCasesForTaskType('rag');
        } else {
            const error = await response.json();
            showAlert('创建失败: ' + (error.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('创建RAG测试用例失败:', error);
        showAlert('创建失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// 运行RAG测试
async function handleRunRagTest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const testCaseId = formData.get('test_case_id');
    const modelName = formData.get('model_name');
    const embeddingModel = formData.get('embedding_model');
    const retrievalStrategy = formData.get('retrieval_strategy');
    
    if (!testCaseId || !modelName) {
        showAlert('请选择测试用例和模型', 'error');
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`/api/rag/test-cases/${testCaseId}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model_name: modelName,
                embedding_model: embeddingModel,
                retrieval_strategy: retrievalStrategy
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            displayTestResult('rag', result);
            loadDashboardData(); // 刷新仪表板数据
        } else {
            const error = await response.json();
            showAlert('测试运行失败: ' + (error.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('运行RAG测试失败:', error);
        showAlert('测试运行失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ==================== Agent任务处理函数 ====================

// 处理Agent表单提交
async function handleAgentFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    let availableTools;
    
    try {
        availableTools = JSON.parse(formData.get('available_tools'));
    } catch (error) {
        showAlert('可用工具JSON格式错误', 'error');
        return;
    }
    
    const testCaseData = {
        name: formData.get('name'),
        description: formData.get('description'),
        task_type: 'agent',
        input_data: {
            task_goal: formData.get('task_goal'),
            available_tools: availableTools,
            initial_state: formData.get('initial_state'),
            agent_type: formData.get('agent_type'),
            max_steps: parseInt(formData.get('max_steps'))
        },
        expected_output: {
            expected_result: formData.get('expected_result'),
            success_criteria: formData.get('success_criteria') ? formData.get('success_criteria').split(',').map(s => s.trim()) : []
        }
    };
    
    try {
        showLoading();
        const response = await fetch('/api/agent/test-cases/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(testCaseData)
        });
        
        if (response.ok) {
            showAlert('Agent测试用例创建成功！', 'success');
            event.target.reset();
            await loadTestCasesForTaskType('agent');
        } else {
            const error = await response.json();
            showAlert('创建失败: ' + (error.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('创建Agent测试用例失败:', error);
        showAlert('创建失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// 运行Agent测试
async function handleRunAgentTest(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const testCaseId = formData.get('test_case_id');
    const modelName = formData.get('model_name');
    const executionMode = formData.get('execution_mode');
    const timeout = parseInt(formData.get('timeout'));
    const verboseLogging = formData.get('verbose_logging') === 'on';
    
    if (!testCaseId || !modelName) {
        showAlert('请选择测试用例和模型', 'error');
        return;
    }
    
    try {
        showLoading();
        const response = await fetch(`/api/agent/test-cases/${testCaseId}/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model_name: modelName,
                execution_mode: executionMode,
                timeout: timeout,
                verbose_logging: verboseLogging
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            displayTestResult('agent', result);
            loadDashboardData(); // 刷新仪表板数据
        } else {
            const error = await response.json();
            showAlert('测试运行失败: ' + (error.detail || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('运行Agent测试失败:', error);
        showAlert('测试运行失败: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ==================== 通用测试结果显示函数 ====================

// 显示测试结果
function displayTestResult(taskType, result) {
    const resultDiv = document.getElementById(`${taskType}-result`);
    const contentDiv = document.getElementById(`${taskType}-result-content`);
    
    if (resultDiv && contentDiv) {
        contentDiv.textContent = JSON.stringify(result, null, 2);
        resultDiv.style.display = 'block';
        
        // 滚动到结果区域
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// ==================== 工具函数 ====================

// 工具函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}