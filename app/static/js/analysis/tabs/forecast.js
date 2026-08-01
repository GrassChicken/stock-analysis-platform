/**
 * 业绩预告渲染模块
 * 
 * 职责:
 * - 渲染业绩预告数据表格
 * - 格式化业绩预告类型、净利润变动、净利润预测
 * 
 * 输入数据格式:
 * {
 *   available: boolean,
 *   data: [
 *     {
 *       ts_code: '000001.SZ',
 *       ann_date: '20240115',
 *       end_date: '20231231',
 *       type: '预增',
 *       p_change_min: 50.0,
 *       p_change_max: 80.0,
 *       net_profit_min: 100000000,
 *       net_profit_max: 120000000,
 *       summary: '业绩大幅增长'
 *     }
 *   ]
 * }
 */

/**
 * 渲染业绩预告内容
 * @param {Object} data - 业绩预告数据
 * @returns {string} HTML 字符串
 */
function renderForecast(data) {
    if (!data || !data.available || !data.data || data.data.length === 0) {
        return '<div class="text-center py-8 text-gray-400">暂无业绩预告数据</div>';
    }
    
    const forecasts = data.data;
    
    // 按报告期排序（最新的在前）
    forecasts.sort((a, b) => {
        const dateA = a.end_date || '';
        const dateB = b.end_date || '';
        return dateB.localeCompare(dateA);
    });
    
    let html = `
        <div class="space-y-4">
            <div class="flex items-center justify-between">
                <h3 class="text-base font-semibold text-gray-700">📊 业绩预告</h3>
                <span class="text-xs text-gray-500">共 ${forecasts.length} 条记录</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-gray-200 text-left">
                            <th class="pb-2 text-gray-600 font-medium">报告期</th>
                            <th class="pb-2 text-gray-600 font-medium">类型</th>
                            <th class="pb-2 text-gray-600 font-medium">净利润变动</th>
                            <th class="pb-2 text-gray-600 font-medium">净利润预测</th>
                            <th class="pb-2 text-gray-600 font-medium">公告日期</th>
                            <th class="pb-2 text-gray-600 font-medium">摘要</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-100">
    `;
    
    forecasts.forEach(forecast => {
        const reportDate = formatDate(forecast.end_date);
        const annDate = formatDate(forecast.ann_date);
        const type = forecast.type || '--';
        const typeClass = getForecastTypeClass(type);
        
        const changeRange = formatForecastChangeRange(forecast.p_change_min, forecast.p_change_max);
        const profitRange = formatForecastProfitRange(forecast.net_profit_min, forecast.net_profit_max);
        const summary = forecast.summary || '--';
        
        html += `
            <tr class="hover:bg-gray-50">
                <td class="py-3 text-gray-700">${reportDate}</td>
                <td class="py-3">
                    <span class="px-2 py-1 text-xs font-medium rounded ${typeClass}">
                        ${type}
                    </span>
                </td>
                <td class="py-3 text-gray-700">${changeRange}</td>
                <td class="py-3 text-gray-700">${profitRange}</td>
                <td class="py-3 text-gray-500">${annDate}</td>
                <td class="py-3 text-gray-600 text-xs max-w-xs truncate" title="${summary}">${summary}</td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    return html;
}

/**
 * 格式化日期（YYYYMMDD -> YYYY-MM-DD）
 * @param {string} dateStr - 日期字符串
 * @returns {string} 格式化后的日期
 */
function formatDate(dateStr) {
    if (!dateStr || dateStr.length !== 8) return '--';
    return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`;
}

/**
 * 获取业绩预告类型的样式类
 * @param {string} type - 预告类型
 * @returns {string} CSS 类名
 */
function getForecastTypeClass(type) {
    const typeMap = {
        '预增': 'bg-red-50 text-red-700',
        '预减': 'bg-green-50 text-green-700',
        '续盈': 'bg-gray-50 text-gray-700',
        '略增': 'bg-red-50 text-red-600',
        '略减': 'bg-green-50 text-green-600',
        '扭亏': 'bg-red-50 text-red-700',
        '首亏': 'bg-green-50 text-green-700',
        '续亏': 'bg-green-50 text-green-700'
    };
    return typeMap[type] || 'bg-gray-50 text-gray-700';
}

/**
 * 格式化净利润变动范围
 * @param {number} min - 最小变动百分比
 * @param {number} max - 最大变动百分比
 * @returns {string} 格式化后的范围
 */
function formatForecastChangeRange(min, max) {
    if (min == null && max == null) return '--';
    
    const formatPercent = (value) => {
        // Tushare p_change_min/max 本身就是百分比值（如 -65.98 表示 -65.98%），不需要再乘100
        const percent = Number(value).toFixed(2);
        const sign = value >= 0 ? '+' : '';
        return `${sign}${percent}%`;
    };
    
    if (min != null && max != null) {
        if (min === max) {
            return formatPercent(min);
        }
        return `${formatPercent(min)} ~ ${formatPercent(max)}`;
    } else if (min != null) {
        return `≥${formatPercent(min)}`;
    } else {
        return `≤${formatPercent(max)}`;
    }
}

/**
 * 格式化净利润预测范围（单位：元 -> 亿元）
 * @param {number} min - 最小值（元）
 * @param {number} max - 最大值（元）
 * @returns {string} 格式化后的范围
 */
function formatForecastProfitRange(min, max) {
    if (min == null && max == null) return '--';
    
    const formatYi = (value) => {
        // Tushare net_profit_min/max 单位是万元，先转为元再转亿
        const yi = (value * 10000) / 100000000;
        return `${yi.toFixed(2)}亿`;
    };
    
    if (min != null && max != null) {
        if (min === max) {
            return formatYi(min);
        }
        return `${formatYi(min)} ~ ${formatYi(max)}`;
    } else if (min != null) {
        return `≥${formatYi(min)}`;
    } else {
        return `≤${formatYi(max)}`;
    }
}
