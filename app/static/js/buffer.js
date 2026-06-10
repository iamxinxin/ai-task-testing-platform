let currentWeekId = null;

const shieldLabels = {
    transfer: '转移盾',
    boundary: '设界盾',
    echo: '听见盾'
};

async function postJson(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || '请求失败');
    }
    return response.json();
}

function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, char => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[char]));
}

function copyText(text) {
    navigator.clipboard?.writeText(text).then(() => {
        alert('已复制，可以去粘贴了');
    }).catch(() => {
        alert('复制失败，请手动选中文案复制');
    });
}

function renderPredictions(data) {
    currentWeekId = data.weekId;
    document.getElementById('energy-mode').textContent = data.energyMode;
    const html = data.predictions.map((item, index) => `
        <div class="prediction-card">
            <div class="d-flex justify-content-between gap-2 align-items-start">
                <div>
                    <span class="badge-probability ${item.probability}">${item.probability}</span>
                    <strong class="ms-2">${escapeHtml(item.scene)}</strong>
                </div>
                <span class="text-muted small">#${index + 1}</span>
            </div>
            <p class="text-muted small mt-2 mb-0">${escapeHtml(item.reason)}</p>
            <div class="shield-grid">
                ${Object.entries(item.shields).map(([type, shield]) => `
                    <div class="shield-item ${type}" data-copy="${escapeHtml(shield.text)}">
                        <div class="shield-label">${shieldLabels[type]}</div>
                        <div class="shield-text">${escapeHtml(shield.text)}</div>
                        <div class="anchor-text">${escapeHtml(shield.anchor)}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
    document.getElementById('prep-results').innerHTML = `
        <div class="alert alert-warning"><strong>能量补给：</strong>${escapeHtml(data.energySupply)}</div>
        ${html}
    `;
    document.querySelectorAll('.shield-item').forEach(el => {
        el.addEventListener('click', () => copyText(el.dataset.copy));
    });
}

function renderShare(data) {
    document.getElementById('share-result').innerHTML = `
        <div class="result-box">
            <div class="shield-label">生成文案</div>
            <div class="shield-text">${escapeHtml(data.selected.text)}</div>
            <p class="anchor-text mb-1"><strong>父母可能反应：</strong>${escapeHtml(data.selected.parentReaction)}</p>
            <p class="anchor-text"><strong>如果被 push：</strong>${escapeHtml(data.selected.replyAdvice)}</p>
            <button class="btn btn-sm buffer-btn" id="copy-share-btn">复制文案</button>
        </div>
    `;
    document.getElementById('copy-share-btn').addEventListener('click', () => copyText(data.selected.text));
}

function renderEmergency(data) {
    const html = data.responses.map(item => `
        <div class="quick-shield ${item.type}" data-copy="${escapeHtml(item.text)}">
            <div class="shield-label">${shieldLabels[item.type]}</div>
            <div class="shield-text">${escapeHtml(item.text)}</div>
            <div class="anchor-text">点击复制</div>
        </div>
    `).join('');
    document.getElementById('emergency-result').innerHTML = `
        <div class="alert alert-light border">
            识别：<strong>${escapeHtml(data.detectedType)}</strong>（置信度 ${Math.round(data.confidence * 100)}%）<br>
            <span class="text-muted">${escapeHtml(data.reminder)}</span>
        </div>
        ${html}
    `;
    document.querySelectorAll('.quick-shield').forEach(el => {
        el.addEventListener('click', () => copyText(el.dataset.copy));
    });
}

async function loadStats() {
    const response = await fetch('/api/buffer/stats');
    const data = await response.json();
    const trend = data.trend.length ? data.trend.map(item => `${item.weekId}: dread ${item.dreadAfter}, push ${item.pushCount}`).join('；') : '暂无复盘记录';
    document.getElementById('stats-result').textContent = `当前 dread：${data.currentDread}/10；近4周：${trend}`;
}

document.addEventListener('DOMContentLoaded', () => {
    const dreadRange = document.getElementById('dread-range');
    const dreadValue = document.getElementById('dread-value');
    dreadRange.addEventListener('input', () => dreadValue.textContent = `${dreadRange.value}/10`);

    document.getElementById('generate-prep-btn').addEventListener('click', async () => {
        const button = document.getElementById('generate-prep-btn');
        button.disabled = true;
        button.textContent = '扫描中...';
        try {
            const data = await postJson('/api/buffer/generate-prep', {
                dread: Number(dreadRange.value),
                lastCallTopics: document.getElementById('last-topics').value
            });
            renderPredictions(data);
        } catch (error) {
            alert(error.message);
        } finally {
            button.disabled = false;
            button.textContent = '扫描本周雷区';
        }
    });

    document.getElementById('translate-share-btn').addEventListener('click', async () => {
        const rawText = document.getElementById('raw-share').value.trim();
        if (!rawText) return alert('先写一件想轻投递的真实状态');
        const data = await postJson('/api/buffer/translate-share', {
            rawText,
            style: document.getElementById('share-style').value
        });
        renderShare(data);
    });

    document.getElementById('emergency-btn').addEventListener('click', async () => {
        const fatherText = document.getElementById('father-text').value.trim();
        if (!fatherText) return alert('先输入父亲刚说的话');
        const data = await postJson('/api/buffer/emergency-shield', { fatherText });
        renderEmergency(data);
    });

    const dumpText = document.getElementById('dump-text');
    dumpText.value = localStorage.getItem('buffer_dump_text') || '';
    document.getElementById('save-dump-btn').addEventListener('click', () => {
        localStorage.setItem('buffer_dump_text', dumpText.value);
        document.getElementById('dump-status').textContent = '已保存到本地浏览器';
    });

    document.getElementById('save-log-btn').addEventListener('click', async () => {
        const data = await postJson('/api/buffer/call-log', {
            weekId: currentWeekId || 'manual-week',
            dreadAfter: Number(document.getElementById('dread-after').value),
            pushCount: Number(document.getElementById('push-count').value),
            shieldUsed: true,
            shieldEffective: true,
            notes: document.getElementById('call-notes').value
        });
        alert(data.message);
        loadStats();
    });

    loadStats();
});
