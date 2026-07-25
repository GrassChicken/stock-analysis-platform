/**
 * 股票对比 PK 模块
 * 
 * 职责:
 * - 搜索并添加对比股票 (2-4 只)
 * - 调用对比 API 获取数据
 * - 渲染对比结果 (表格 + 雷达图)
 */

// 已选股票代码列表
const selectedCodes = [];
let radarChart = null;

// ==================== 搜索 ====================

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('search-input');
    const resultsBox = document.getElementById('search-results');
    let debounceTimer = null;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const keyword = input.value.trim();
            if (!keyword) {
                resultsBox.classList.add('hidden');
                return;
            }
            fetchSearch(keyword);
        }, 300);
    });

    // 点击外部关闭搜索结果
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#search-results') && !e.target.closest('#search-input')) {
            resultsBox.classList.add('hidden');
        }
    });

    // 对比按钮
    document.getElementById('compare-btn').addEventListener('click', startCompare);
});

async function fetchSearch(keyword) {
    try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(keyword)}`);
        const data = await res.json();
        renderSearchResults(data.results || []);
    } catch (err) {
        console.error('搜索失败:', err);
    }
}

function renderSearchResults(results) {
    const box = document.getElementById('search-results');
    
    if (results.length === 0) {
        box.innerHTML = '<div class="text-center py-4 text-gray-400 text-sm">未找到相关股票</div>';
        box.classList.remove('hidden');
        return;
    }

    const items = results.map(stock => {
        const isSelected = selectedCodes.includes(stock.code);
        const isDisabled = !isSelected && selectedCodes.length >= 4;
        return `
            <div class="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition ${isDisabled ? 'opacity-40' : ''}">
                <div class="flex-1">
                    <span class="font-semibold text-gray-800">${stock.name}</span>
                    <span class="text-xs text-gray-500 ml-2">${stock.code}</span>
                    ${stock.industry ? `<span class="text-xs text-gray-400 ml-2">${stock.industry}</span>` : ''}
                </div>
                <button onclick="addStock('${stock.code}', '${stock.name}')"
                        class="px-3 py-1 text-xs rounded-full ${isSelected ? 'bg-green-100 text-green-700' : isDisabled ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-primary-100 text-primary-700 hover:bg-primary-200'}"
                        ${isDisabled ? 'disabled' : ''}>
                    ${isSelected ? '✓ 已添加' : isDisabled ? '已满' : '+ 添加'}
                </button>
            </div>
        `;
    }).join('');

    box.innerHTML = `<div class="space-y-1 max-h-64 overflow-y-auto border border-gray-100 rounded-lg">${items}</div>`;
    box.classList.remove('hidden');
}

// ==================== 选择管理 ====================

function addStock(code, name) {
    if (selectedCodes.includes(code)) return;
    if (selectedCodes.length >= 4) return;

    selectedCodes.push(code);
    updateSelectedUI();
    
    // 关闭搜索结果
    document.getElementById('search-results').classList.add('hidden');
    document.getElementById('search-input').value = '';
}

function removeStock(code) {
    const idx = selectedCodes.indexOf(code);
    if (idx > -1) {
        selectedCodes.splice(idx, 1);
        updateSelectedUI();
    }
}

function updateSelectedUI() {
    const container = document.getElementById('selected-stocks');
    const btn = document.getElementById('compare-btn');

    if (selectedCodes.length === 0) {
        container.innerHTML = '<span class="text-sm text-gray-400">暂未选择股票</span>';
        btn.disabled = true;
        btn.textContent = '开始对比分析';
    } else {
        // 从 API 获取股票名称可能较慢，先用代码显示
        container.innerHTML = selectedCodes.map(code => `
            <span class="inline-flex items-center px-3 py-1.5 bg-primary-50 text-primary-700 rounded-full text-sm font-medium">
                <span id="tag-${code}">${code}</span>
                <button onclick="removeStock('${code}')" class="ml-2 text-primary-400 hover:text-primary-700">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </span>
        `).join('');
        
        if (selectedCodes.length >= 2) {
            btn.disabled = false;
            btn.textContent = `开始对比分析 (${selectedCodes.length} 只)`;
        } else {
            btn.disabled = true;
            btn.textContent = `还需选择 ${2 - selectedCodes.length} 只股票`;
        }
    }
}

// ==================== 对比分析 ====================

async function startCompare() {
    if (selectedCodes.length < 2) return;

    const btn = document.getElementById('compare-btn');
    btn.disabled = true;
    btn.textContent = '分析中，请稍候...';

    try {
        const res = await fetch('/api/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codes: selectedCodes })
        });
        const data = await res.json();

        if (data.error) {
            alert('对比失败: ' + data.error);
            btn.disabled = false;
            btn.textContent = '开始对比分析';
            return;
        }

        // 更新股票名称标签
        updateStockNames(data.stocks || []);
        
        // 渲染对比结果
        renderCompareResults(data);
        
        // 显示结果区域
        document.getElementById('compare-results').classList.remove('hidden');
        
        // 滚动到结果区域
        document.getElementById('compare-results').scrollIntoView({ behavior: 'smooth' });
    } catch (err) {
        console.error('对比失败:', err);
        alert('网络错误，请重试');
    } finally {
        btn.disabled = false;
        btn.textContent = `开始对比分析 (${selectedCodes.length} 只)`;
    }
}

function updateStockNames(stocks) {
    stocks.forEach(stock => {
        const tag = document.getElementById(`tag-${stock.code}`);
        if (tag && stock.name) {
            tag.textContent = `${stock.name} (${stock.code})`;
        }
    });
}

// ==================== 结果渲染 ====================

function renderCompareResults(data) {
    const stocks = data.stocks || [];
    const best = data.best || {};

    // AI 总结
    document.getElementById('ai-summary').textContent = data.summary || '暂无分析总结';

    // 综合评分对比表
    renderScoreTable(stocks, best);

    // 关键指标对比表
    renderMetricsTable(stocks, best);

    // 雷达图
    renderRadarChart(stocks);
}

function renderScoreTable(stocks, best) {
    const thead = document.querySelector('#score-table').parentElement.querySelector('thead tr');
    const tbody = document.getElementById('score-table');

    // 构建表头
    let headerHtml = '<th class="text-left py-3 px-2 font-semibold text-gray-600">指标</th>';
    stocks.forEach((s, i) => {
        const colors = ['text-blue-600', 'text-green-600', 'text-purple-600', 'text-orange-600'];
        headerHtml += `<th class="text-center py-3 px-2 font-semibold ${colors[i % 4]}">${s.name || s.code}</th>`;
    });
    thead.innerHTML = headerHtml;

    // 维度名称映射
    const dimNames = {
        total_score: '综合评分',
        fundamental_score: '基本面',
        technical_score: '技术面',
        valuation_score: '估值面',
        capital_score: '资金面',
        industry_score: '行业面',
        growth_score: '成长性'
    };

    // 构建数据行
    let rows = '';
    const dimensions = ['total_score', 'fundamental_score', 'technical_score', 'valuation_score', 'capital_score', 'industry_score', 'growth_score'];
    
    dimensions.forEach(dim => {
        let row = `<tr class="border-b border-gray-50 hover:bg-gray-50"><td class="py-2.5 px-2 text-gray-600 font-medium">${dimNames[dim] || dim}</td>`;
        
        // 找最大值用于高亮
        const values = stocks.map(s => {
            if (dim === 'total_score') return s.total_score || 0;
            return (s.breakdown && s.breakdown[dim]) || 0;
        });
        const maxVal = Math.max(...values);

        stocks.forEach((s, i) => {
            const val = dim === 'total_score' ? (s.total_score || 0) : ((s.breakdown && s.breakdown[dim]) || 0);
            const isBest = val === maxVal && val > 0;
            const rating = dim === 'total_score' ? ` <span class="text-xs text-gray-400">(${s.rating || '--'})</span>` : '';
            row += `<td class="text-center py-2.5 px-2 ${isBest ? 'font-bold text-rise' : 'text-gray-700'}">${val.toFixed(1)}${rating}</td>`;
        });
        
        row += '</tr>';
        rows += row;
    });

    tbody.innerHTML = rows;
}

function renderMetricsTable(stocks, best) {
    const thead = document.querySelector('#metrics-table').parentElement.querySelector('thead tr');
    const tbody = document.getElementById('metrics-table');

    // 构建表头
    let headerHtml = '<th class="text-left py-3 px-2 font-semibold text-gray-600">指标</th>';
    stocks.forEach((s, i) => {
        const colors = ['text-blue-600', 'text-green-600', 'text-purple-600', 'text-orange-600'];
        headerHtml += `<th class="text-center py-3 px-2 font-semibold ${colors[i % 4]}">${s.name || s.code}</th>`;
    });
    thead.innerHTML = headerHtml;

    const fmt = (v, unit = '') => {
        if (v == null || v === 0) return '--';
        return typeof v === 'number' ? v.toFixed(2) + unit : v;
    };
    const fmtWan = (v) => {
        if (!v) return '--';
        return (v / 10000).toFixed(0) + '亿';
    };

    // 指标行定义
    const metrics = [
        { label: '股价', key: 'price', format: v => fmt(v, '元'), path: 'price' },
        { label: '涨跌幅', key: 'change_pct', format: v => fmt(v, '%'), path: 'change_pct', colored: true },
        { label: 'ROE', key: 'roe', format: v => fmt(v, '%'), path: 'fundamental.roe' },
        { label: '净利率', key: 'net_margin', format: v => fmt(v, '%'), path: 'fundamental.net_margin' },
        { label: '毛利率', key: 'gross_margin', format: v => fmt(v, '%'), path: 'fundamental.gross_margin' },
        { label: '营收同比', key: 'revenue_yoy', format: v => fmt(v, '%'), path: 'fundamental.revenue_yoy', colored: true },
        { label: '利润同比', key: 'profit_yoy', format: v => fmt(v, '%'), path: 'fundamental.profit_yoy', colored: true },
        { label: '资产负债率', key: 'debt_ratio', format: v => fmt(v, '%'), path: 'fundamental.debt_ratio' },
        { label: 'PE (TTM)', key: 'pe_ttm', format: v => fmt(v), path: 'valuation.pe_ttm' },
        { label: 'PB', key: 'pb', format: v => fmt(v), path: 'valuation.pb' },
        { label: 'PS', key: 'ps', format: v => fmt(v), path: 'valuation.ps' },
        { label: 'PE 分位', key: 'pe_pct', format: v => fmt(v, '%'), path: 'valuation.pe_percentile' },
        { label: 'PB 分位', key: 'pb_pct', format: v => fmt(v, '%'), path: 'valuation.pb_percentile' },
        { label: '总市值', key: 'total_mv', format: fmtWan, path: 'valuation.total_mv' },
    ];

    let rows = '';
    metrics.forEach(m => {
        let row = `<tr class="border-b border-gray-50 hover:bg-gray-50"><td class="py-2.5 px-2 text-gray-600 font-medium">${m.label}</td>`;

        stocks.forEach(s => {
            // 通过路径获取值
            const val = m.path.split('.').reduce((obj, key) => obj && obj[key], s);
            let text = m.format(val);
            let cls = 'text-gray-700';
            
            if (m.colored && typeof val === 'number') {
                cls = val > 0 ? 'text-rise font-semibold' : val < 0 ? 'text-fall font-semibold' : 'text-gray-700';
            }

            row += `<td class="text-center py-2.5 px-2 ${cls}">${text}</td>`;
        });

        row += '</tr>';
        rows += row;
    });

    tbody.innerHTML = rows;
}

function renderRadarChart(stocks) {
    const dom = document.getElementById('radar-chart');
    radarChart = echarts.getInstanceByDom(dom) || echarts.init(dom);

    const colors = ['#3b82f6', '#22c55e', '#a855f7', '#f97316'];
    const dims = [
        { key: 'fundamental_score', name: '基本面' },
        { key: 'technical_score', name: '技术面' },
        { key: 'valuation_score', name: '估值面' },
        { key: 'capital_score', name: '资金面' },
        { key: 'industry_score', name: '行业面' },
        { key: 'growth_score', name: '成长性' }
    ];

    const seriesData = stocks.map((s, i) => ({
        value: dims.map(d => (s.breakdown && s.breakdown[d.key]) || 0),
        name: s.name || s.code,
        lineStyle: { color: colors[i], width: 2 },
        areaStyle: { color: colors[i], opacity: 0.15 },
        itemStyle: { color: colors[i] },
        symbol: 'circle',
        symbolSize: 6
    }));

    radarChart.setOption({
        tooltip: {
            trigger: 'item'
        },
        legend: {
            data: stocks.map(s => s.name || s.code),
            bottom: 0,
            textStyle: { fontSize: 12 }
        },
        radar: {
            center: ['50%', '45%'],
            radius: '65%',
            indicator: dims.map(d => ({ name: d.name, max: 100 })),
            axisName: {
                color: '#666',
                fontSize: 13,
                fontWeight: 500
            },
            splitArea: {
                areaStyle: {
                    color: ['rgba(59, 130, 246, 0.03)', 'rgba(59, 130, 246, 0.06)']
                }
            },
            axisLine: { lineStyle: { color: 'rgba(0,0,0,0.08)' } },
            splitLine: { lineStyle: { color: 'rgba(0,0,0,0.08)' } }
        },
        series: [{
            type: 'radar',
            data: seriesData
        }]
    });

    // 响应式
    window.addEventListener('resize', () => {
        if (radarChart) radarChart.resize();
    });
}
