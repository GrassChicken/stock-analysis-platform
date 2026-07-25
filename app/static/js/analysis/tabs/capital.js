/**
 * 资金面分析渲染模块
 * 
 * 职责:
 * - 渲染资金面分析内容（资金评分、筹码集中度、北向持股、资金流向、融资融券、筹码分布）
 */

/**
 * 渲染资金面分析内容
 * @param {Object} data - 资金面数据
 * @returns {string} HTML 字符串
 */
function renderCapital(data) {
    if (!data || data.error) return '<div class="text-center py-8 text-gray-400">暂无数据</div>';
    
    const moneyFlow = data.money_flow || {};
    const northFlow = data.north_flow || {};
    const margin = data.margin || {};
    const chipDist = data.chip_distribution || {};
    const capitalScore = data.capital_score || {};
    
    const fmt = (v, unit = '') => v != null ? (typeof v === 'number' ? v.toFixed(2) + unit : v) : '--';
    const fmtWan = (v) => {
        if (v == null) return '--';
        return (v / 10000).toFixed(2) + '万';
    };
    
    const flowColor = (v) => v > 0 ? 'text-rise' : v < 0 ? 'text-fall' : 'text-gray-600';
    
    return `
    <!-- 资金面评分 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-blue-700 mb-2">资金面评分</h4>
            <div class="text-2xl sm:text-3xl font-bold text-blue-900">${fmt(capitalScore.total)}</div>
            <div class="text-xs sm:text-sm text-blue-600 mt-1">${capitalScore.rating || '--'}</div>
        </div>
        <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-green-700 mb-2">筹码集中度</h4>
            <div class="text-xl sm:text-2xl font-bold text-green-900">${chipDist.concentration || '--'}</div>
            <div class="text-xs sm:text-sm text-green-600 mt-1">${chipDist.price_position || '--'}</div>
        </div>
        <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-purple-700 mb-2">北向持股</h4>
            <div class="text-xl sm:text-2xl font-bold text-purple-900">${fmt(northFlow.hold_ratio, '%')}</div>
            <div class="text-xs sm:text-sm text-purple-600 mt-1">${northFlow.date ? northFlow.date.slice(4, 6) + '-' + northFlow.date.slice(6, 8) : '--'}</div>
        </div>
    </div>

    <!-- 资金流向 + 融资融券 + 筹码分布 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- 主力资金流向 -->
        ${moneyFlow.available ? `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">💰 主力资金流向 <span class="${flowColor(moneyFlow.main_net_inflow)} font-normal">(${moneyFlow.trend || '--'})</span></h4>
            <div class="space-y-2 text-xs sm:text-sm">
                <div class="flex justify-between items-center"><span class="text-gray-500">主力净流入</span><span class="font-semibold tabular-nums ${flowColor(moneyFlow.main_net_inflow)}">${fmtWan(moneyFlow.main_net_inflow)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">主力占比</span><span class="font-semibold tabular-nums">${fmt(moneyFlow.main_net_inflow_pct, '%')}</span></div>
                <div class="border-t pt-2 mt-2">
                    <div class="flex justify-between items-center"><span class="text-gray-500">超大单</span><span class="font-semibold tabular-nums ${flowColor(moneyFlow.super_large_net)}">${fmtWan(moneyFlow.super_large_net)}</span></div>
                    <div class="flex justify-between items-center"><span class="text-gray-500">大单</span><span class="font-semibold tabular-nums ${flowColor(moneyFlow.large_net)}">${fmtWan(moneyFlow.large_net)}</span></div>
                    <div class="flex justify-between items-center"><span class="text-gray-500">中单</span><span class="font-semibold tabular-nums ${flowColor(moneyFlow.medium_net)}">${fmtWan(moneyFlow.medium_net)}</span></div>
                    <div class="flex justify-between items-center"><span class="text-gray-500">小单</span><span class="font-semibold tabular-nums ${flowColor(moneyFlow.small_net)}">${fmtWan(moneyFlow.small_net)}</span></div>
                </div>
            </div>
            <div class="mt-3 pt-2 border-t text-[10px] text-gray-400 leading-relaxed">
                <span class="font-medium text-gray-500">📋 统计规则(Tushare):</span> 小单&lt;5万 | 中单5~20万 | 大单20~100万 | 特大单≥100万 | 主力=大单+特大单
            </div>
        </div>
        ` : `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">💰 主力资金流向</h4>
            <div class="text-center py-8 text-gray-400 text-xs sm:text-sm">数据源连接失败<br>请稍后重试</div>
        </div>
        `}

        <!-- 融资融券 -->
        ${margin.available ? `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📊 融资融券 <span class="${margin.net_margin > 0 ? 'text-rise' : 'text-fall'} font-normal">(${margin.trend || '--'})</span></h4>
            <div class="space-y-2 text-xs sm:text-sm">
                <div class="flex justify-between items-center"><span class="text-gray-500">融资余额</span><span class="font-semibold tabular-nums">${fmtWan(margin.margin_balance)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">融资买入</span><span class="font-semibold tabular-nums">${fmtWan(margin.margin_buy)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">融资偿还</span><span class="font-semibold tabular-nums">${fmtWan(margin.margin_repay)}</span></div>
                <div class="flex justify-between items-center border-t pt-2 mt-2"><span class="text-gray-500">融资净买入</span><span class="font-semibold tabular-nums ${flowColor(margin.net_margin)}">${fmtWan(margin.net_margin)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">融券余额</span><span class="font-semibold tabular-nums">${fmtWan(margin.short_balance)}</span></div>
            </div>
        </div>
        ` : `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📊 融资融券</h4>
            <div class="text-center py-8 text-gray-400 text-xs sm:text-sm">暂无数据</div>
        </div>
        `}

        <!-- 筹码分布 -->
        ${chipDist.available ? `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">🎯 筹码分布</h4>
            <div class="space-y-2 text-xs sm:text-sm">
                <div class="flex justify-between items-center"><span class="text-gray-500">当前价格</span><span class="font-semibold tabular-nums">${fmt(chipDist.current_price)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">60日高点</span><span class="font-semibold tabular-nums text-rise">${fmt(chipDist.high_60d)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">60日低点</span><span class="font-semibold tabular-nums text-fall">${fmt(chipDist.low_60d)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">平均成本</span><span class="font-semibold tabular-nums">${fmt(chipDist.avg_cost)}</span></div>
                <div class="border-t pt-2 mt-2">
                    <div class="flex justify-between items-center"><span class="text-gray-500">获利盘</span><span class="font-semibold tabular-nums text-rise">${fmt(chipDist.profit_ratio, '%')}</span></div>
                    <div class="flex justify-between items-center"><span class="text-gray-500">套牢盘</span><span class="font-semibold tabular-nums text-fall">${fmt(chipDist.loss_ratio, '%')}</span></div>
                </div>
            </div>
        </div>
        ` : `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">🎯 筹码分布</h4>
            <div class="text-center py-8 text-gray-400 text-xs sm:text-sm">暂无数据</div>
        </div>
        `}
    </div>
    `;
}
