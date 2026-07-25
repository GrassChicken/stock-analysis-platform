/**
 * 估值分析渲染模块
 * 
 * 职责:
 * - 渲染股票估值分析内容（当前估值指标、历史分位）
 * 
 * 输入数据格式:
 * {
 *   code: "000001.SZ",
 *   current_valuation: { pe_ttm, pe, pb, ps, total_mv, circ_mv, ... },
 *   historical_percentile: { pe_percentile, pb_percentile, ... },
 *   peg: 1.56,
 *   dcf_valuation: { ... },
 *   rating: "低估"
 * }
 */

/**
 * 渲染估值分析内容
 * @param {Object} data - 估值数据
 * @returns {string} HTML 字符串
 */
function renderValuation(data) {
    if (!data || data.error) return '<div class="text-center py-8 text-gray-400">暂无数据</div>';
    
    const v = data.current_valuation || {};
    const hist = data.historical_percentile || {};
    const fmt = (val, unit = '') => val != null ? val.toFixed(2) + unit : '--';
    
    // 市值已经是亿元（后端已转换）
    const fmtMv = (val) => val ? fmt(val, '亿') : '--';
    
    const pctColor = (pct) => pct < 30 ? 'text-green-600' : pct > 70 ? 'text-red-600' : 'text-yellow-600';
    const pctLabel = (pct) => pct < 30 ? '低估' : pct > 70 ? '高估' : '合理';
    const fmtPct = (val) => val != null ? val.toFixed(1) + '%' : '--';
    
    return `
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3"> 当前估值</h4>
            <div class="grid grid-cols-2 gap-3 text-sm">
                <div class="flex justify-between"><span class="text-gray-500">PE (TTM)</span><span class="font-semibold">${fmt(v.pe_ttm)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">PE</span><span class="font-semibold">${fmt(v.pe)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">PB</span><span class="font-semibold">${fmt(v.pb)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">PS</span><span class="font-semibold">${fmt(v.ps)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">总市值</span><span class="font-semibold">${fmtMv(v.total_mv)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">流通市值</span><span class="font-semibold">${fmtMv(v.circ_mv)}</span></div>
            </div>
        </div>
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📈 历史分位</h4>
            <div class="space-y-4 text-sm">
                <div>
                    <div class="flex justify-between mb-1"><span class="text-gray-500">PE 分位</span><span class="font-semibold ${pctColor(hist.pe_percentile)}">${fmtPct(hist.pe_percentile)} <span class="text-xs ${pctColor(hist.pe_percentile)}">${pctLabel(hist.pe_percentile)}</span></span></div>
                    <div class="w-full bg-gray-200 rounded-full h-2"><div class="bg-blue-500 h-2 rounded-full" style="width: ${hist.pe_percentile || 0}%"></div></div>
                </div>
                <div>
                    <div class="flex justify-between mb-1"><span class="text-gray-500">PB 分位</span><span class="font-semibold ${pctColor(hist.pb_percentile)}">${fmtPct(hist.pb_percentile)} <span class="text-xs ${pctColor(hist.pb_percentile)}">${pctLabel(hist.pb_percentile)}</span></span></div>
                    <div class="w-full bg-gray-200 rounded-full h-2"><div class="bg-blue-500 h-2 rounded-full" style="width: ${hist.pb_percentile || 0}%"></div></div>
                </div>
            </div>
        </div>
    </div>`;
}
