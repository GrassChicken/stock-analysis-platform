/**
 * 行业面分析渲染模块
 * 
 * 职责:
 * - 渲染行业面分析内容（行业评分、行业特征、行业内对比、行业趋势、概念标签）
 */

/**
 * 渲染行业面分析内容
 * @param {Object} data - 行业面数据
 * @returns {string} HTML 字符串
 */
function renderIndustry(data) {
    if (!data || data.error) return '<div class="text-center py-8 text-gray-400">暂无数据</div>';
    
    const industryInfo = data.industry_info || {};
    const peerComparison = data.peer_comparison || {};
    const industryTrend = data.industry_trend || {};
    const conceptTags = data.concept_tags || {};
    const industryScore = data.industry_score || {};
    
    const fmt = (v, unit = '') => v != null ? (typeof v === 'number' ? v.toFixed(2) + unit : v) : '--';
    
    const trendColor = (trend) => {
        if (trend === '热门') return 'text-rise';
        if (trend === '冷门') return 'text-fall';
        return 'text-yellow-600';
    };
    
    return `
    <!-- 行业面评分 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-blue-700 mb-2">行业面评分</h4>
            <div class="text-2xl sm:text-3xl font-bold text-blue-900">${fmt(industryScore.total)}</div>
            <div class="text-xs sm:text-sm text-blue-600 mt-1">${industryScore.rating || '--'}</div>
        </div>
        <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-green-700 mb-2">所属行业</h4>
            <div class="text-xl sm:text-2xl font-bold text-green-900">${industryInfo.industry_name || '--'}</div>
            <div class="text-xs sm:text-sm text-green-600 mt-1">${industryInfo.market_position || '--'}</div>
        </div>
        <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-5 text-center">
            <h4 class="text-sm font-semibold text-purple-700 mb-2">行业趋势</h4>
            <div class="text-xl sm:text-2xl font-bold text-purple-900 ${trendColor(industryTrend.trend)}">${industryTrend.trend || '--'}</div>
            <div class="text-xs sm:text-sm text-purple-600 mt-1">关注度 ${fmt(industryTrend.market_attention)}</div>
        </div>
    </div>

    <!-- 行业详情 -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- 行业特征 -->
        ${industryInfo.available ? `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">🏭 行业特征</h4>
            <div class="space-y-2 text-xs sm:text-sm">
                <div class="flex justify-between items-center"><span class="text-gray-500">行业名称</span><span class="font-semibold">${industryInfo.industry_name || '--'}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">行业描述</span><span class="font-semibold">${industryInfo.industry_desc || '--'}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">行业权重</span><span class="font-semibold tabular-nums">${fmt(industryInfo.industry_weight)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">市场地位</span><span class="font-semibold">${industryInfo.market_position || '--'}</span></div>
            </div>
        </div>
        ` : `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">🏭 行业特征</h4>
            <div class="text-center py-8 text-gray-400 text-xs sm:text-sm">暂无数据</div>
        </div>
        `}

        <!-- 行业内对比 -->
        ${peerComparison.available ? `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📊 行业内对比 (共 ${peerComparison.peer_count} 家)</h4>
            <div class="space-y-2 text-xs sm:text-sm">
                <div class="flex justify-between items-center"><span class="text-gray-500">PE排名</span><span class="font-semibold">第 ${peerComparison.pe_rank} 名 (${fmt(peerComparison.pe_percentile, '%')})</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">PB排名</span><span class="font-semibold">第 ${peerComparison.pb_rank} 名 (${fmt(peerComparison.pb_percentile, '%')})</span></div>
                <div class="flex justify-between items-center border-t pt-2 mt-2"><span class="text-gray-500">当前PE</span><span class="font-semibold tabular-nums">${fmt(peerComparison.current.pe)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">当前PB</span><span class="font-semibold tabular-nums">${fmt(peerComparison.current.pb)}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">总市值</span><span class="font-semibold tabular-nums">${(peerComparison.current.total_mv / 100000000).toFixed(2)}亿</span></div>
            </div>
        </div>
        ` : `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📊 行业内对比</h4>
            <div class="text-center py-8 text-gray-400 text-xs sm:text-sm">暂无数据</div>
        </div>
        `}

        <!-- 行业趋势 -->
        ${industryTrend.available ? `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📈 行业趋势</h4>
            <div class="space-y-2 text-xs sm:text-sm">
                <div class="flex justify-between items-center"><span class="text-gray-500">当前趋势</span><span class="font-semibold ${trendColor(industryTrend.trend)}">${industryTrend.trend || '--'}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">趋势描述</span><span class="font-semibold">${industryTrend.trend_desc || '--'}</span></div>
                <div class="flex justify-between items-center"><span class="text-gray-500">市场关注度</span><span class="font-semibold tabular-nums">${fmt(industryTrend.market_attention)}</span></div>
            </div>
        </div>
        ` : `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">📈 行业趋势</h4>
            <div class="text-center py-8 text-gray-400 text-xs sm:text-sm">暂无数据</div>
        </div>
        `}

        <!-- 概念标签 -->
        ${conceptTags.available ? `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">🏷️ 概念标签</h4>
            <div class="flex flex-wrap gap-2 mt-3">
                ${conceptTags.concepts.map(tag => `
                    <span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium">${tag}</span>
                `).join('')}
            </div>
        </div>
        ` : `
        <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">🏷️ 概念标签</h4>
            <div class="text-center py-8 text-gray-400 text-xs sm:text-sm">暂无数据</div>
        </div>
        `}
    </div>
    `;
}
