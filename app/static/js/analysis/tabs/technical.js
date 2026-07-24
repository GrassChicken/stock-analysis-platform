/**
 * 技术面分析渲染模块
 * 
 * 职责:
 * - 渲染技术面分析内容（技术评分、买卖信号、均线、MACD、KDJ、RSI、布林带、量价分析）
 * - 展示K线形态识别结果
 * - 展示支撑阻力位
 * 
 * 输入数据格式:
 * {
 *   ma: { values, arrangement, above_ma_count, total_ma_count },
 *   macd: { dif, dea, macd, zero_axis_position, histogram_trend, golden_cross, death_cross, divergence },
 *   kdj: { k, d, j, zone, golden_cross, death_cross },
 *   rsi: { values, zone },
 *   boll: { upper, mid, lower, pb, bandwidth },
 *   volume: { volume_ratio, vol_status, coordination, vol_trend_5d },
 *   patterns: [{ name, desc, signal, reliability }],
 *   signals: { action, bullish_count, bearish_count, bullish_signals, bearish_signals },
 *   score: { total, rating },
 *   support_resistance: { supports, resistances }
 * }
 */

/**
 * 渲染技术面分析内容
 * @param {Object} data - 技术面数据
 * @returns {string} HTML 字符串
 */
function renderTechnical(data) {
    if (!data || data.error) return '<div class="text-center py-8 text-gray-400">暂无数据</div>';

    const ma = data.ma || {};
    const macd = data.macd || {};
    const kdj = data.kdj || {};
    const rsi = data.rsi || {};
    const boll = data.boll || {};
    const volume = data.volume || {};
    const patterns = data.patterns || [];
    const signals = data.signals || {};
    const score = data.score || {};

    const fmt = (v, unit = '') => v != null ? (typeof v === 'number' ? v.toFixed(2) + unit : v) : '--';

    // 信号颜色映射
    const signalColor = (action) => {
        if (['strong_buy', 'buy'].includes(action)) return 'text-rise bg-red-50';
        if (['strong_sell', 'sell'].includes(action)) return 'text-fall bg-green-50';
        return 'text-yellow-600 bg-yellow-50';
    };

    const signalText = {
        'strong_buy': '强烈看多',
        'buy': '偏多',
        'sell': '偏空',
        'strong_sell': '强烈看空',
        'hold': '观望'
    };

    // 排列状态
    const arrText = { 'bullish': '多头排列', 'bearish': '空头排列', 'mixed': '交叉排列' };
    const arrColor = { 'bullish': 'text-rise', 'bearish': 'text-fall', 'mixed': 'text-yellow-600' };

    // 区域状态
    const zoneText = { 'overbought': '超买', 'oversold': '超卖', 'strong': '强势', 'weak': '弱势', 'neutral': '中性' };
    const zoneColor = { 'overbought': 'text-rise', 'oversold': 'text-fall', 'strong': 'text-orange-600', 'weak': 'text-fall', 'neutral': 'text-gray-600' };

    return `
    <!-- 综合评分 + 买卖信号 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-blue-700 mb-2">技术评分</h4>
            <div class="text-2xl sm:text-3xl font-bold text-blue-900">${score.total || '--'}</div>
            <div class="text-xs sm:text-sm text-blue-600 mt-1">${score.rating || '--'}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-gray-600 mb-2">买卖信号</h4>
            <div class="text-base sm:text-xl font-bold ${signalColor(signals.action)} rounded px-3 py-1">${signalText[signals.action] || '--'}</div>
            <div class="text-xs text-gray-500 mt-2">看多 ${signals.bullish_count || 0} / 看空 ${signals.bearish_count || 0}</div>
        </div>
        <div class="bg-gray-50 rounded-lg p-5">
            <h4 class="text-sm font-semibold text-gray-600 mb-2">信号明细</h4>
            <div class="space-y-1 text-xs">
                ${(signals.bullish_signals || []).map(s => `<div class="text-rise">▲ ${s}</div>`).join('')}
                ${(signals.bearish_signals || []).map(s => `<div class="text-fall">▼ ${s}</div>`).join('')}
            </div>
        </div>
    </div>

    <!-- 技术指标 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <!-- 均线系统 -->
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📊 均线系统 <span class="${arrColor[ma.arrangement] || ''} font-normal">(${arrText[ma.arrangement] || '--'})</span></h4>
            <div class="space-y-2 text-sm">
                ${Object.entries(ma.values || {}).map(([k, v]) => `
                    <div class="flex justify-between">
                        <span class="text-gray-500">${k.toUpperCase()}</span>
                        <span class="font-semibold tabular-nums">${fmt(v)}</span>
                    </div>
                `).join('')}
                <div class="flex justify-between border-t pt-2 mt-2">
                    <span class="text-gray-500">站上均线数</span>
                    <span class="font-semibold">${ma.above_ma_count || 0}/${ma.total_ma_count || 0}</span>
                </div>
            </div>
        </div>

        <!-- MACD -->
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📈 MACD</h4>
            <div class="space-y-2 text-sm">
                <div class="flex justify-between"><span class="text-gray-500">DIF</span><span class="font-semibold tabular-nums">${fmt(macd.dif)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">DEA</span><span class="font-semibold tabular-nums">${fmt(macd.dea)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">MACD柱</span><span class="font-semibold tabular-nums ${macd.macd >= 0 ? 'text-rise' : 'text-fall'}">${fmt(macd.macd)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">零轴位置</span><span class="font-semibold">${macd.zero_axis_position === 'above' ? '上方' : '下方'}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">柱状趋势</span><span class="font-semibold">${macd.histogram_trend === 'expanding' ? '扩张' : '收缩'}</span></div>
                ${macd.golden_cross ? '<div class="text-rise text-xs font-semibold">🔺 金叉</div>' : ''}
                ${macd.death_cross ? '<div class="text-fall text-xs font-semibold">🔻 死叉</div>' : ''}
                ${macd.divergence?.desc ? `<div class="text-xs text-orange-600">⚠️ ${macd.divergence.desc}</div>` : ''}
            </div>
        </div>

        <!-- KDJ -->
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📉 KDJ <span class="${zoneColor[kdj.zone] || ''} font-normal">(${zoneText[kdj.zone] || '--'})</span></h4>
            <div class="space-y-2 text-sm">
                <div class="flex justify-between"><span class="text-gray-500">K</span><span class="font-semibold tabular-nums">${fmt(kdj.k)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">D</span><span class="font-semibold tabular-nums">${fmt(kdj.d)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">J</span><span class="font-semibold tabular-nums">${fmt(kdj.j)}</span></div>
                ${kdj.golden_cross ? '<div class="text-rise text-xs font-semibold">🔺 金叉</div>' : ''}
                ${kdj.death_cross ? '<div class="text-fall text-xs font-semibold">🔻 死叉</div>' : ''}
            </div>
        </div>

        <!-- RSI -->
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">💪 RSI <span class="${zoneColor[rsi.zone] || ''} font-normal">(${zoneText[rsi.zone] || '--'})</span></h4>
            <div class="space-y-2 text-sm">
                ${Object.entries(rsi.values || {}).map(([k, v]) => `
                    <div class="flex justify-between">
                        <span class="text-gray-500">${k.toUpperCase()}</span>
                        <span class="font-semibold tabular-nums">${fmt(v)}</span>
                    </div>
                `).join('')}
            </div>
        </div>

        <!-- 布林带 -->
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">🎯 布林带</h4>
            <div class="space-y-2 text-sm">
                <div class="flex justify-between"><span class="text-gray-500">上轨</span><span class="font-semibold tabular-nums text-rise">${fmt(boll.upper)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">中轨</span><span class="font-semibold tabular-nums">${fmt(boll.mid)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">下轨</span><span class="font-semibold tabular-nums text-fall">${fmt(boll.lower)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">%B位置</span><span class="font-semibold tabular-nums">${fmt(boll.pb)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">带宽</span><span class="font-semibold tabular-nums">${fmt(boll.bandwidth, '%')}</span></div>
            </div>
        </div>

        <!-- 量价分析 -->
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📊 量价分析</h4>
            <div class="space-y-2 text-sm">
                <div class="flex justify-between"><span class="text-gray-500">量比</span><span class="font-semibold tabular-nums">${fmt(volume.volume_ratio)}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">量能状态</span><span class="font-semibold">${volume.vol_status || '--'}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">量价配合</span><span class="font-semibold">${volume.coordination || '--'}</span></div>
                <div class="flex justify-between"><span class="text-gray-500">5日量变化</span><span class="font-semibold tabular-nums">${fmt(volume.vol_trend_5d, '%')}</span></div>
            </div>
        </div>
    </div>

    <!-- K线形态识别 -->
    ${patterns.length > 0 ? `
    <div class="mt-4 bg-gray-50 rounded-lg p-4">
        <h4 class="text-sm font-semibold text-gray-600 mb-3">🕯️ K线形态识别</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            ${patterns.map(p => `
                <div class="bg-white rounded p-3 border-l-4 ${p.signal === 'bullish' ? 'border-rise' : p.signal === 'bearish' ? 'border-fall' : 'border-yellow-400'}">
                    <div class="font-semibold text-sm">${p.name}</div>
                    <div class="text-xs text-gray-500 mt-1">${p.desc}</div>
                    <div class="text-xs mt-1 ${p.signal === 'bullish' ? 'text-rise' : p.signal === 'bearish' ? 'text-fall' : 'text-yellow-600'}">${p.signal === 'bullish' ? '看多' : p.signal === 'bearish' ? '看空' : '中性'} · 可靠性: ${p.reliability}</div>
                </div>
            `).join('')}
        </div>
    </div>
    ` : ''}

    <!-- 支撑阻力位 -->
    <div class="mt-4 bg-gray-50 rounded-lg p-4">
        <h4 class="text-sm font-semibold text-gray-600 mb-3">🎚️ 支撑阻力位</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
                <h5 class="text-xs font-semibold text-fall mb-2">阻力位</h5>
                <div class="space-y-1">
                    ${(data.support_resistance?.resistances || []).map(r => `
                        <div class="flex justify-between text-sm bg-red-50 rounded px-3 py-1">
                            <span class="text-gray-600">${r.type}</span>
                            <span class="font-semibold tabular-nums text-fall">${r.price}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div>
                <h5 class="text-xs font-semibold text-rise mb-2">支撑位</h5>
                <div class="space-y-1">
                    ${(data.support_resistance?.supports || []).map(s => `
                        <div class="flex justify-between text-sm bg-green-50 rounded px-3 py-1">
                            <span class="text-gray-600">${s.type}</span>
                            <span class="font-semibold tabular-nums text-rise">${s.price}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    </div>
    `;
}
