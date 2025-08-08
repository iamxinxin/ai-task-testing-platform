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
    loadClassificationTestCases();
    setupEventListeners();
}

// 设置事件监听器
function setupEventListeners() {
    // 分类任务表单提交
    document.getElementById('classification-form').addEventListener('submit', handleClassificationFormSubmit);
    
    // 运行分类测试表单提交
    document.getElementById('run-classification-test').addEventListener('submit', handleRunClassificationTest);
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
async function loadClassificationTestCases() {
    try {
        const response = await fetch('/api/classification/test-cases/');
        const data = await response.json();
        
        const select = document.querySelector('select[name="test_case_id"]');
        select.innerHTML = '<option value="">请选择测试用例</option>';
        
        data.forEach(testCase => {
            const option = document.createElement('option');
            option.value = testCase.id;
            option.textContent = testCase.name;
            select.appendChild(option);
        });
        
    } catch (error) {
        console.error('加载分类测试用例失败:', error);
    }
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