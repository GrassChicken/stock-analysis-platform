/**
 * 基本面分析渲染模块
 * 
 * 职责:
 * - 渲染股票基本面分析内容（盈利能力、成长性、偿债能力、现金流）
 * 
 * 输入数据格式:
 * {
 *   profitability: { roe, net_margin, eps, ... },
 *   growth: { revenue_yoy, profit_yoy, profit_continuous_growth_quarters, ... },
 *   solvency: { debt_to_assets, current_ratio, ... },
 *   cashflow: { operating_cashflow, free_cashflow, invest_cashflow, cashflow_coverage }
 * }
 */

/**
 * 渲染基本面分析内容
 * @param {Object} data - 基本面数据
 * @returns {string} HTML 字符串
 */
function renderFundamental(data) {
    if (!data || data.error) return '<div class="text-center py-8 text-gray-400">暂无数据</div>';
    
    const p = data.profitability || {};
    const g = data.growth || {};
    const s = data.solvency || {};
    const c = data.cashflow || {};
    const fmt = (v, unit = '') => v != null ? v.toFixed(2) + unit : '--';
    
    return `
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">💰 盈利能力</h4>
            <div class="space-y-2 text-xs sm:text-sm">
                <div class="flex justify-between items-center"><span class="text-gray-500">ROE</span><span class="font-semibold">${fmt(p.roe, '%')}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">净利率</span><span class="font-semibold">${fmt(p.net_margin, '%')}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">EPS</span><span class="font-semibold">${fmt(p.eps, '元')}</span></div>
            </div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📈 成长性</h4>
            <div class="space-y-2 text-xs sm:text-sm">
                <div class="flex justify-between items-center"><span class="text-gray-500">营收同比</span><span class="font-semibold ${g.revenue_yoy >= 0 ? 'text-rise' : 'text-fall'}">${fmt(g.revenue_yoy, '%')}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">利润同比</span><span class="font-semibold ${g.profit_yoy >= 0 ? 'text-rise' : 'text-fall'}">${fmt(g.profit_yoy, '%')}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">连续增长</span><span class="font-semibold">${g.profit_continuous_growth_quarters || 0} 季</span></div>
            </div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">🏦 偿债能力</h4>
            <div class="space-y-2 text-xs sm:text-sm">
                <div class="flex justify-between items-center"><span class="text-gray-500">资产负债率</span><span class="font-semibold">${fmt(s.debt_to_assets, '%')}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">流动比率</span><span class="font-semibold">${fmt(s.current_ratio)}</span></div>
            </div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4 md:col-span-2 lg:col-span-3">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">💵 现金流</h4>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 text-xs sm:text-sm">
                <div><span class="text-gray-500 block">经营现金流</span><span class="font-semibold">${(c.operating_cashflow || 0).toLocaleString()} 万</span></div>
                <div><span class="text-gray-500 block">自由现金流</span><span class="font-semibold ${(c.free_cashflow || 0) >= 0 ? 'text-rise' : 'text-fall'}">${(c.free_cashflow || 0).toLocaleString()} 万</span></div>
                <div><span class="text-gray-500 block">投资现金流</span><span class="font-semibold">${(c.invest_cashflow || 0).toLocaleString()} 万</span></div>
                <div><span class="text-gray-500 block">现金流覆盖率</span><span class="font-semibold">${fmt(c.cashflow_coverage, '%')}</span></div>
            </div>
        </div>
    </div>`;
}
