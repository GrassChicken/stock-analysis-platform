/**
 * 财务状况渲染模块
 *
 * 职责:
 * - 渲染财务状况分析内容（营收/利润趋势、毛利率/净利率走势、财务健康度）
 *
 * 设计:
 * - renderFinance() 只返回 HTML 字符串（不含 <script>）
 * - initFinanceCharts() 在 HTML 插入后初始化 ECharts
 * - 这样避免了 innerHTML 插入 script 不执行的问题
 */

/**
 * 格式化大数字（万元/亿元）
 */
function fmtMoney(val) {
    if (val == null || isNaN(val)) return '--';
    const abs = Math.abs(val);
    if (abs >= 100000000) return (val / 100000000).toFixed(2) + '亿';
    if (abs >= 10000) return (val / 10000).toFixed(2) + '万';
    return val.toFixed(2);
}

/**
 * 格式化百分比
 */
function fmtPct(val) {
    if (val == null || isNaN(val)) return '--';
    return val.toFixed(2) + '%';
}

/**
 * 格式化季度日期为简短标签
 */
function fmtQuarter(dateStr) {
    if (!dateStr) return '';
    const y = dateStr.substring(0, 4);
    const m = dateStr.substring(4, 6);
    const quarterMap = { '03': 'Q1', '06': 'Q2', '09': 'Q3', '12': 'Q4' };
    return y + (quarterMap[m] || '');
}

/**
 * 从累计数据拆解单季度数据
 */
function calcSingleQuarter(incomeData) {
    if (!incomeData || incomeData.length === 0) return [];

    // 按 end_date 升序排序
    const sorted = [...incomeData].sort((a, b) => a.end_date.localeCompare(b.end_date));
    const result = [];

    for (let i = 0; i < sorted.length; i++) {
        const cur = sorted[i];
        const month = cur.end_date.substring(4, 6);

        if (month === '03') {
            result.push({
                end_date: cur.end_date,
                revenue: cur.revenue || cur.total_revenue || 0,
                n_income: cur.n_income || 0,
                n_income_attr_p: cur.n_income_attr_p || 0,
                oper_cost: cur.oper_cost || 0
            });
        } else {
            const curYear = cur.end_date.substring(0, 4);
            const prevMap = { '06': '0331', '09': '0630', '12': '0930' };
            const prevEndDate = curYear + prevMap[month];
            const prev = sorted.find(d => d.end_date === prevEndDate);

            if (prev) {
                result.push({
                    end_date: cur.end_date,
                    revenue: (cur.revenue || cur.total_revenue || 0) - (prev.revenue || prev.total_revenue || 0),
                    n_income: (cur.n_income || 0) - (prev.n_income || 0),
                    n_income_attr_p: (cur.n_income_attr_p || 0) - (prev.n_income_attr_p || 0),
                    oper_cost: (cur.oper_cost || 0) - (prev.oper_cost || 0)
                });
            } else {
                result.push({
                    end_date: cur.end_date,
                    revenue: cur.revenue || cur.total_revenue || 0,
                    n_income: cur.n_income || 0,
                    n_income_attr_p: cur.n_income_attr_p || 0,
                    oper_cost: cur.oper_cost || 0
                });
            }
        }
    }

    return result;
}

/**
 * 渲染财务状况内容（只返回 HTML，不含 script）
 */
function renderFinance(data) {
    if (!data || data.error) {
        return '<div class="text-center py-8 text-gray-400">暂无财务数据</div>';
    }

    const indicators = data.indicators || [];
    const income = data.income || [];
    const balance = data.balance || [];
    const cashflow = data.cashflow || [];

    if (indicators.length === 0 && income.length === 0) {
        return '<div class="text-center py-8 text-gray-400">暂无财务数据</div>';
    }

    const singleIncome = calcSingleQuarter(income);

    let html = '';

    // 1. 核心指标卡片
    html += renderFinanceCards(indicators, singleIncome);

    // 2. 营收+利润趋势（只输出容器 div）
    if (singleIncome.length > 0) {
        html += `
        <div class="bg-gray-50 rounded-lg p-3 sm:p-4 mb-5">
            <h4 class="text-sm font-semibold text-gray-700 mb-3">📈 营收 & 净利润趋势（单季度）</h4>
            <div id="finance-revenue-chart" style="width:100%;height:280px;"></div>
        </div>`;
    }

    // 3. 盈利能力趋势
    if (indicators.length > 0) {
        html += `
        <div class="bg-gray-50 rounded-lg p-3 sm:p-4 mb-5">
            <h4 class="text-sm font-semibold text-gray-700 mb-3">📊 盈利能力趋势</h4>
            <div id="finance-margin-chart" style="width:100%;height:280px;"></div>
        </div>`;
    }

    // 4. 同比增长趋势
    if (indicators.length >= 2) {
        html += `
        <div class="bg-gray-50 rounded-lg p-3 sm:p-4 mb-5">
            <h4 class="text-sm font-semibold text-gray-700 mb-3">📈 同比增长趋势</h4>
            <div id="finance-growth-chart" style="width:100%;height:260px;"></div>
        </div>`;
    }

    // 5. 现金流趋势
    if (cashflow.length > 0) {
        html += `
        <div class="bg-gray-50 rounded-lg p-3 sm:p-4 mb-5">
            <h4 class="text-sm font-semibold text-gray-700 mb-3">💵 现金流趋势</h4>
            <div id="finance-cashflow-chart" style="width:100%;height:280px;"></div>
        </div>`;
    }

    // 6. 财务健康度表格
    html += renderHealthTable(indicators);

    return `<div>${html}</div>`;
}

/**
 * 渲染核心指标卡片
 */
function renderFinanceCards(indicators, singleIncome) {
    if (!indicators || indicators.length === 0) return '';

    const latest = indicators[0];
    const latestIncome = singleIncome.length > 0 ? singleIncome[singleIncome.length - 1] : null;
    const prevIncome = singleIncome.length > 1 ? singleIncome[singleIncome.length - 2] : null;

    const revenue = latestIncome ? latestIncome.revenue : 0;
    const netProfit = latestIncome ? latestIncome.n_income_attr_p : 0;

    let revenueYoY = latest.tr_yoy;
    let profitYoY = latest.dt_netprofit_yoy;

    let revenueQoQ = null;
    let profitQoQ = null;
    if (latestIncome && prevIncome && prevIncome.revenue !== 0) {
        revenueQoQ = ((latestIncome.revenue - prevIncome.revenue) / Math.abs(prevIncome.revenue)) * 100;
    }
    if (latestIncome && prevIncome && prevIncome.n_income_attr_p !== 0) {
        profitQoQ = ((latestIncome.n_income_attr_p - prevIncome.n_income_attr_p) / Math.abs(prevIncome.n_income_attr_p)) * 100;
    }

    const arrow = (v) => v > 0 ? '↑' : v < 0 ? '↓' : '→';
    const colorClass = (v) => v > 0 ? 'text-rise' : v < 0 ? 'text-fall' : 'text-gray-500';

    return `
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-3 sm:p-4">
            <div class="text-xs text-gray-500 mb-1">📊 营业收入(单季)</div>
            <div class="text-base sm:text-lg font-bold text-gray-800">${fmtMoney(revenue)}</div>
            <div class="text-xs mt-1 ${colorClass(revenueYoY)}">${revenueYoY != null ? '同比 ' + arrow(revenueYoY) + ' ' + fmtPct(revenueYoY) : ''}</div>
            <div class="text-xs ${colorClass(revenueQoQ)}">${revenueQoQ != null ? '环比 ' + arrow(revenueQoQ) + ' ' + fmtPct(revenueQoQ) : ''}</div>
        </div>
        <div class="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-lg p-3 sm:p-4">
            <div class="text-xs text-gray-500 mb-1">💰 净利润(单季)</div>
            <div class="text-base sm:text-lg font-bold text-gray-800">${fmtMoney(netProfit)}</div>
            <div class="text-xs mt-1 ${colorClass(profitYoY)}">${profitYoY != null ? '同比 ' + arrow(profitYoY) + ' ' + fmtPct(profitYoY) : ''}</div>
            <div class="text-xs ${colorClass(profitQoQ)}">${profitQoQ != null ? '环比 ' + arrow(profitQoQ) + ' ' + fmtPct(profitQoQ) : ''}</div>
        </div>
        <div class="bg-gradient-to-br from-amber-50 to-amber-100 rounded-lg p-3 sm:p-4">
            <div class="text-xs text-gray-500 mb-1">📈 毛利率</div>
            <div class="text-base sm:text-lg font-bold text-gray-800">${fmtPct(latest.grossprofit_margin)}</div>
            <div class="text-xs mt-1 text-gray-500">净利率 ${fmtPct(latest.netprofit_margin)}</div>
        </div>
        <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-3 sm:p-4">
            <div class="text-xs text-gray-500 mb-1">🏦 ROE</div>
            <div class="text-base sm:text-lg font-bold text-gray-800">${fmtPct(latest.roe)}</div>
            <div class="text-xs mt-1 text-gray-500">负债率 ${fmtPct(latest.debt_to_assets)}</div>
        </div>
    </div>`;
}

/**
 * 渲染财务健康度表格
 */
function renderHealthTable(indicators) {
    if (!indicators || indicators.length === 0) return '';

    const latest = indicators[0];

    let debtRating, debtColor;
    if (latest.debt_to_assets == null || isNaN(latest.debt_to_assets) || latest.debt_to_assets === 0) {
        debtRating = '--'; debtColor = 'text-gray-400';
    } else if (latest.debt_to_assets < 30) {
        debtRating = '保守'; debtColor = 'text-emerald-600';
    } else if (latest.debt_to_assets < 50) {
        debtRating = '稳健'; debtColor = 'text-blue-600';
    } else if (latest.debt_to_assets < 70) {
        debtRating = '适中'; debtColor = 'text-amber-600';
    } else {
        debtRating = '偏高'; debtColor = 'text-red-500';
    }

    const rows = [
        { label: '资产负债率', val: fmtPct(latest.debt_to_assets), rating: debtRating, color: debtColor },
        { label: '流动比率', val: latest.current_ratio ? latest.current_ratio.toFixed(2) : '--', rating: latest.current_ratio > 2 ? '安全' : latest.current_ratio > 1.5 ? '良好' : latest.current_ratio > 1 ? '一般' : '偏高', color: latest.current_ratio > 2 ? 'text-emerald-600' : latest.current_ratio > 1.5 ? 'text-blue-600' : latest.current_ratio > 1 ? 'text-amber-600' : 'text-red-500' },
        { label: '速动比率', val: latest.quick_ratio ? latest.quick_ratio.toFixed(2) : '--', rating: latest.quick_ratio > 1.5 ? '安全' : latest.quick_ratio > 1 ? '良好' : latest.quick_ratio > 0.5 ? '一般' : '偏高', color: latest.quick_ratio > 1.5 ? 'text-emerald-600' : latest.quick_ratio > 1 ? 'text-blue-600' : latest.quick_ratio > 0.5 ? 'text-amber-600' : 'text-red-500' },
        { label: '毛利率', val: fmtPct(latest.grossprofit_margin), rating: latest.grossprofit_margin > 40 ? '优秀' : latest.grossprofit_margin > 25 ? '良好' : latest.grossprofit_margin > 15 ? '一般' : latest.grossprofit_margin > 0 ? '偏低' : '--', color: latest.grossprofit_margin > 40 ? 'text-emerald-600' : latest.grossprofit_margin > 25 ? 'text-blue-600' : latest.grossprofit_margin > 15 ? 'text-amber-600' : latest.grossprofit_margin > 0 ? 'text-red-500' : 'text-gray-400' },
        { label: '净利率', val: fmtPct(latest.netprofit_margin), rating: latest.netprofit_margin > 20 ? '优秀' : latest.netprofit_margin > 10 ? '良好' : latest.netprofit_margin > 5 ? '一般' : '偏低', color: latest.netprofit_margin > 20 ? 'text-emerald-600' : latest.netprofit_margin > 10 ? 'text-blue-600' : latest.netprofit_margin > 5 ? 'text-amber-600' : 'text-red-500' },
        { label: 'ROE', val: fmtPct(latest.roe), rating: latest.roe > 20 ? '优秀' : latest.roe > 15 ? '良好' : latest.roe > 8 ? '一般' : '偏低', color: latest.roe > 20 ? 'text-emerald-600' : latest.roe > 15 ? 'text-blue-600' : latest.roe > 8 ? 'text-amber-600' : 'text-red-500' },
    ];

    return `
    <div class="bg-gray-50 rounded-lg p-3 sm:p-4">
        <h4 class="text-sm font-semibold text-gray-700 mb-3">🏥 财务健康度</h4>
        <div class="overflow-x-auto">
            <table class="w-full text-xs sm:text-sm">
                <thead>
                    <tr class="text-left text-gray-500 border-b">
                        <th class="pb-2 pr-3">指标</th>
                        <th class="pb-2 pr-3 text-right">当前值</th>
                        <th class="pb-2 text-right">评级</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(r => `
                    <tr class="border-b border-gray-100">
                        <td class="py-2 pr-3 text-gray-600">${r.label}</td>
                        <td class="py-2 pr-3 text-right font-semibold">${r.val}</td>
                        <td class="py-2 text-right"><span class="${r.color} font-medium">${r.rating}</span></td>
                    </tr>`).join('')}
                </tbody>
            </table>
        </div>
        <div class="mt-3 text-xs text-gray-400">* 评级标准仅供参考，不同行业差异较大</div>
    </div>`;
}

// ==================== 图表初始化（HTML 插入后调用） ====================

/**
 * 初始化财务状况页的所有图表
 * 由 analysis-tabs.js 在 innerHTML 设置后调用
 */
function initFinanceCharts(data) {
    if (!data) return;

    const indicators = data.indicators || [];
    const income = data.income || [];
    const cashflow = data.cashflow || [];
    const singleIncome = calcSingleQuarter(income);

    // 营收 & 净利润趋势
    const revEl = document.getElementById('finance-revenue-chart');
    if (revEl && singleIncome.length > 0) {
        initRevenueChart(revEl, singleIncome);
    }

    // 盈利能力趋势
    const marginEl = document.getElementById('finance-margin-chart');
    if (marginEl && indicators.length > 0) {
        initMarginChart(marginEl, indicators);
    }

    // 同比增长趋势
    const growthEl = document.getElementById('finance-growth-chart');
    if (growthEl && indicators.length >= 2) {
        initGrowthChart(growthEl, indicators);
    }

    // 现金流趋势
    const cfEl = document.getElementById('finance-cashflow-chart');
    if (cfEl && cashflow.length > 0) {
        initCashflowChart(cfEl, cashflow);
    }
}

function initRevenueChart(el, singleIncome) {
    const chart = echarts.init(el);
    const labels = singleIncome.map(d => fmtQuarter(d.end_date));
    const revenues = singleIncome.map(d => d.revenue);
    const profits = singleIncome.map(d => d.n_income_attr_p);

    chart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
            formatter: function(params) {
                var s = params[0].axisValue + '<br/>';
                params.forEach(function(p) {
                    var val = p.value;
                    var unit = '元';
                    if (Math.abs(val) >= 100000000) { val = (val / 100000000).toFixed(2); unit = '亿'; }
                    else if (Math.abs(val) >= 10000) { val = (val / 10000).toFixed(2); unit = '万'; }
                    s += p.marker + ' ' + p.seriesName + ': ' + val + unit + '<br/>';
                });
                return s;
            }
        },
        legend: { data: ['营业收入', '净利润'], bottom: 0, textStyle: { fontSize: 11 } },
        grid: { left: 10, right: 10, top: 20, bottom: 40, containLabel: true },
        xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, rotate: window.innerWidth < 640 ? 30 : 0 } },
        yAxis: { type: 'value', axisLabel: { fontSize: 10, formatter: function(v) {
            if (Math.abs(v) >= 100000000) return (v / 100000000).toFixed(0) + '亿';
            if (Math.abs(v) >= 10000) return (v / 10000).toFixed(0) + '万';
            return v;
        }}},
        series: [
            { name: '营业收入', type: 'bar', data: revenues, itemStyle: { color: '#3B82F6', borderRadius: [4,4,0,0] }, barMaxWidth: 40 },
            { name: '净利润', type: 'bar', data: profits, itemStyle: { color: '#10B981', borderRadius: [4,4,0,0] }, barMaxWidth: 40 }
        ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
}

function initMarginChart(el, indicators) {
    const chart = echarts.init(el);
    const sorted = [...indicators].sort((a, b) => a.end_date.localeCompare(b.end_date));
    const labels = sorted.map(d => fmtQuarter(d.end_date));
    const grossMargins = sorted.map(d => d.grossprofit_margin);
    const netMargins = sorted.map(d => d.netprofit_margin);
    const roeData = sorted.map(d => d.roe);

    chart.setOption({
        tooltip: { trigger: 'axis', formatter: function(params) {
            var s = params[0].axisValue + '<br/>';
            params.forEach(function(p) {
                if (p.value != null) s += p.marker + ' ' + p.seriesName + ': ' + p.value.toFixed(2) + '%<br/>';
            });
            return s;
        }},
        legend: { data: ['毛利率', '净利率', 'ROE'], bottom: 0, textStyle: { fontSize: 11 } },
        grid: { left: 10, right: 10, top: 20, bottom: 40, containLabel: true },
        xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, rotate: window.innerWidth < 640 ? 30 : 0 }, boundaryGap: false },
        yAxis: { type: 'value', axisLabel: { fontSize: 10, formatter: '{value}%' } },
        series: [
            { name: '毛利率', type: 'line', data: grossMargins, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 }, itemStyle: { color: '#F59E0B' } },
            { name: '净利率', type: 'line', data: netMargins, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 }, itemStyle: { color: '#3B82F6' } },
            { name: 'ROE', type: 'line', data: roeData, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 }, itemStyle: { color: '#8B5CF6' } }
        ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
}

function initGrowthChart(el, indicators) {
    const chart = echarts.init(el);
    const sorted = [...indicators].sort((a, b) => a.end_date.localeCompare(b.end_date));
    const labels = sorted.map(d => fmtQuarter(d.end_date));
    const revenueGrowth = sorted.map(d => d.tr_yoy);
    const profitGrowth = sorted.map(d => d.dt_netprofit_yoy);

    chart.setOption({
        tooltip: { trigger: 'axis', formatter: function(params) {
            var s = params[0].axisValue + '<br/>';
            params.forEach(function(p) {
                if (p.value != null) s += p.marker + ' ' + p.seriesName + ': ' + p.value.toFixed(2) + '%<br/>';
            });
            return s;
        }},
        legend: { data: ['营收同比增长', '净利润同比增长'], bottom: 0, textStyle: { fontSize: 11 } },
        grid: { left: 10, right: 10, top: 20, bottom: 40, containLabel: true },
        xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, rotate: window.innerWidth < 640 ? 30 : 0 }, boundaryGap: false },
        yAxis: { type: 'value', axisLabel: { fontSize: 10, formatter: '{value}%' }, splitLine: { lineStyle: { type: 'dashed' } } },
        series: [
            { name: '营收同比增长', type: 'line', data: revenueGrowth, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 }, itemStyle: { color: '#3B82F6' }, markLine: { silent: true, data: [{ yAxis: 0 }], lineStyle: { type: 'dashed', color: '#9CA3AF' }, label: { show: false } } },
            { name: '净利润同比增长', type: 'line', data: profitGrowth, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { width: 2 }, itemStyle: { color: '#F59E0B' } }
        ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
}

function initCashflowChart(el, cashflow) {
    const chart = echarts.init(el);
    const sorted = [...cashflow].sort((a, b) => a.end_date.localeCompare(b.end_date));
    const labels = sorted.map(d => fmtQuarter(d.end_date));
    const operating = sorted.map(d => d.n_cashflow_act);
    const investing = sorted.map(d => d.n_cashflow_inv_act);
    const financing = sorted.map(d => d.n_cash_flows_fnc_act);

    chart.setOption({
        tooltip: { trigger: 'axis', formatter: function(params) {
            var s = params[0].axisValue + '<br/>';
            params.forEach(function(p) {
                if (p.value != null) {
                    var val = p.value;
                    var unit = '元';
                    if (Math.abs(val) >= 100000000) { val = (val / 100000000).toFixed(2); unit = '亿'; }
                    else if (Math.abs(val) >= 10000) { val = (val / 10000).toFixed(2); unit = '万'; }
                    s += p.marker + ' ' + p.seriesName + ': ' + val + unit + '<br/>';
                }
            });
            return s;
        }},
        legend: { data: ['经营活动', '投资活动', '筹资活动'], bottom: 0, textStyle: { fontSize: 11 } },
        grid: { left: 10, right: 10, top: 20, bottom: 40, containLabel: true },
        xAxis: { type: 'category', data: labels, axisLabel: { fontSize: 10, rotate: window.innerWidth < 640 ? 30 : 0 } },
        yAxis: { type: 'value', axisLabel: { fontSize: 10, formatter: function(v) {
            if (Math.abs(v) >= 100000000) return (v / 100000000).toFixed(0) + '亿';
            if (Math.abs(v) >= 10000) return (v / 10000).toFixed(0) + '万';
            return v;
        }}},
        series: [
            { name: '经营活动', type: 'bar', stack: 'cf', data: operating, itemStyle: { color: '#10B981' } },
            { name: '投资活动', type: 'bar', stack: 'cf', data: investing, itemStyle: { color: '#EF4444' } },
            { name: '筹资活动', type: 'bar', stack: 'cf', data: financing, itemStyle: { color: '#6366F1', borderRadius: [4,4,0,0] } }
        ]
    });
    window.addEventListener('resize', function() { chart.resize(); });
}
