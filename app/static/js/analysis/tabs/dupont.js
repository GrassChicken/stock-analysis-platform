/**
 * 杜邦分析渲染模块
 * 
 * 职责:
 * - 渲染杜邦分析内容（ROE分解、净利率、权益乘数）
 */

/**
 * 渲染杜邦分析内容
 * @param {Object} data - 杜邦分析数据
 * @returns {string} HTML 字符串
 */
function renderDupont(data) {
    if (!data || data.error) return '<div class="text-center py-8 text-gray-400">暂无数据</div>';
    const r = data.roe_components || {};
    const c = data.contribution || {};
    const fmt = (v, unit = '') => v != null ? v.toFixed(2) + unit : '--';
    return `
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-blue-700 mb-2">ROE (净资产收益率)</h4>
            <div class="text-2xl sm:text-3xl font-bold text-blue-900">${fmt(r.roe, '%')}</div>
        </div>
        <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-green-700 mb-2">净利率</h4>
            <div class="text-xl sm:text-2xl font-bold text-green-900">${fmt(r.net_margin, '%')}</div>
        </div>
        <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-purple-700 mb-2">权益乘数</h4>
            <div class="text-xl sm:text-2xl font-bold text-purple-900">${fmt(r.equity_multiplier)}</div>
        </div>
    </div>
    <div class="mt-4 bg-gray-50 rounded-lg p-4">
        <h4 class="text-sm font-semibold text-gray-600 mb-3">📊 杜邦分解</h4>
        <p class="text-xs sm:text-sm text-gray-600 mb-2"><span class="font-semibold">ROE</span> = <span class="text-green-600">净利率</span> × <span class="text-purple-600">总资产周转率</span> × <span class="text-blue-600">权益乘数</span></p>
        <p class="text-xs sm:text-sm text-gray-600 mb-4">${fmt(r.net_margin, '%')} × ${fmt(r.asset_turn)} × ${fmt(r.equity_multiplier)} = <span class="font-bold text-blue-700">${fmt(r.roe, '%')}</span></p>
        ${c.main_driver ? `<div class="text-xs sm:text-sm"><span class="font-semibold">主要驱动因素:</span> <span class="text-primary-600">${c.main_driver}</span></div>` : ''}
    </div>`;
}
