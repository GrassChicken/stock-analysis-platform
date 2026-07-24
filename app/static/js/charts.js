// 数字滚动动画
function animateNumber(element, target, duration = 1000, decimals = 0) {
    const start = 0;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // easeOutQuart 缓动
        const easeOut = 1 - Math.pow(1 - progress, 4);
        const current = start + (target - start) * easeOut;
        element.textContent = current.toFixed(decimals);
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

/**
 * ECharts 图表封装
 * K线/雷达/资金流向等图表的通用配置
 */

// 涨跌颜色
const RISE_COLOR = '#ef4444';
const FALL_COLOR = '#22c55e';

/**
 * K线图配置
 */
function createKlineOption(data) {
    const dates = data.map(d => {
        const raw = d.trade_date || d.date || '';
        // "20260717" -> "07-17"
        if (raw.length === 8) return raw.slice(4, 6) + '-' + raw.slice(6, 8);
        return raw;
    });
    const ohlc = data.map(d => [d.open, d.close, d.low, d.high]);
    const volumes = data.map(d => d.vol || d.volume);

    return {
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross', crossStyle: { color: '#999' } },
            backgroundColor: 'rgba(255,255,255,0.98)',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            padding: [12, 16],
            textStyle: { color: '#1f2937', fontSize: 13 },
            extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,0.08); border-radius: 8px;',
            formatter: function(params) {
                if (!params || params.length === 0) return '';
                const date = params[0].axisValue;
                let html = `<div style="font-weight:600;color:#6b7280;margin-bottom:8px;font-size:12px">${date}</div>`;
                params.forEach(p => {
                    if (p.seriesType === 'candlestick' && p.data) {
                        const [open, close, low, high] = p.data;
                        const change = close - open;
                        const pct = ((change / open) * 100).toFixed(2);
                        const color = change >= 0 ? RISE_COLOR : FALL_COLOR;
                        const arrow = change >= 0 ? '▲' : '▼';
                        html += `<div style="margin-bottom:10px">`;
                        html += `<div style="display:flex;justify-content:space-between;gap:24px;margin-bottom:4px"><span style="color:#6b7280">开</span><span style="font-weight:600;color:#1f2937">${open.toFixed(2)}</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;gap:24px;margin-bottom:4px"><span style="color:#6b7280">收</span><span style="font-weight:600;color:${color}">${close.toFixed(2)} <span style="font-size:11px">${arrow} ${pct}%</span></span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;gap:24px;margin-bottom:4px"><span style="color:#6b7280">高</span><span style="font-weight:600;color:#1f2937">${high.toFixed(2)}</span></div>`;
                        html += `<div style="display:flex;justify-content:space-between;gap:24px"><span style="color:#6b7280">低</span><span style="font-weight:600;color:#1f2937">${low.toFixed(2)}</span></div>`;
                        html += `</div>`;
                    }
                    if (p.seriesType === 'bar' && p.seriesName === '成交量') {
                        const vol = p.data;
                        html += `<div style="display:flex;justify-content:space-between;gap:24px;padding-top:8px;border-top:1px dashed #e5e7eb"><span style="color:#6b7280">成交量</span><span style="font-weight:600;color:#1f2937">${(vol / 10000).toFixed(2)}万手</span></div>`;
                    }
                });
                return html;
            }
        },
        grid: [
            { left: '8%', right: '3%', top: '5%', height: '60%' },
            { left: '8%', right: '3%', top: '72%', height: '18%' }
        ],
        xAxis: [
            { type: 'category', data: dates, gridIndex: 0, boundaryGap: true, axisLine: { lineStyle: { color: '#e5e7eb' } } },
            { type: 'category', data: dates, gridIndex: 1, boundaryGap: true, axisLine: { lineStyle: { color: '#e5e7eb' } } }
        ],
        yAxis: [
            { type: 'value', gridIndex: 0, splitLine: { lineStyle: { color: '#f3f4f6' } } },
            { type: 'value', gridIndex: 1, splitLine: { lineStyle: { color: '#f3f4f6' } } }
        ],
        series: [
            {
                name: 'K线',
                type: 'candlestick',
                data: ohlc,
                xAxisIndex: 0,
                yAxisIndex: 0,
                itemStyle: {
                    color: RISE_COLOR,
                    color0: FALL_COLOR,
                    borderColor: RISE_COLOR,
                    borderColor0: FALL_COLOR
                }
            },
            {
                name: '成交量',
                type: 'bar',
                data: volumes,
                xAxisIndex: 1,
                yAxisIndex: 1,
                itemStyle: {
                    color: function(params) {
                        const idx = params.dataIndex;
                        return ohlc[idx][1] >= ohlc[idx][0] ? RISE_COLOR : FALL_COLOR;
                    }
                }
            }
        ],
        dataZoom: [
            { type: 'inside', xAxisIndex: [0, 1], start: 70, end: 100 },
            { type: 'slider', xAxisIndex: [0, 1], start: 70, end: 100, bottom: '2%' }
        ]
    };
}

/**
 * 雷达图配置
 */
function createRadarOption(scores) {
    return {
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(255,255,255,0.98)',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            padding: [10, 14],
            textStyle: { color: '#1f2937', fontSize: 13 },
            extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,0.08); border-radius: 8px;',
            formatter: function(params) {
                if (!params || !params.data) return '';
                const dims = ['基本面', '技术面', '资金面', '估值面', '行业面'];
                const vals = params.data.value;
                let html = `<div style="font-weight:600;color:#2563eb;margin-bottom:8px">六维评分</div>`;
                dims.forEach((name, i) => {
                    const v = vals[i] || 0;
                    const color = v >= 80 ? '#16a34a' : v >= 60 ? '#2563eb' : v >= 40 ? '#ca8a04' : '#dc2626';
                    const bar = `<div style="width:60px;height:6px;background:#f1f5f9;border-radius:3px;display:inline-block;vertical-align:middle;margin-left:6px"><div style="width:${v}%;height:100%;background:${color};border-radius:3px"></div></div>`;
                    html += `<div style="display:flex;justify-content:space-between;gap:16px;margin-bottom:4px;align-items:center"><span style="color:#6b7280">${name}</span><span style="font-weight:600;color:#1f2937">${v.toFixed(1)}${bar}</span></div>`;
                });
                return html;
            }
        },
        radar: {
            indicator: [
                { name: '基本面', max: 100 },
                { name: '技术面', max: 100 },
                { name: '资金面', max: 100 },
                { name: '估值面', max: 100 },
                { name: '行业面', max: 100 }
            ],
            shape: 'polygon',
            splitArea: {
                areaStyle: { color: ['#f8fafc', '#f1f5f9', '#e2e8f0', '#cbd5e1'] }
            },
            axisLine: { lineStyle: { color: '#e2e8f0' } },
            splitLine: { lineStyle: { color: '#e2e8f0' } }
        },
        series: [{
            type: 'radar',
            data: [{
                value: scores || [0, 0, 0, 0, 0],
                name: '评分',
                areaStyle: {
                    color: 'rgba(37, 99, 235, 0.15)'
                },
                lineStyle: { color: '#2563eb', width: 2 },
                itemStyle: { color: '#2563eb' }
            }]
        }]
    };
}

/**
 * 资金流向图配置
 */
function createCapitalFlowOption(data) {
    return {
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(255,255,255,0.98)',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            padding: [10, 14],
            textStyle: { color: '#1f2937', fontSize: 13 },
            extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,0.08); border-radius: 8px;',
            formatter: function(params) {
                if (!params || params.length === 0) return '';
                const date = params[0].axisValue;
                let html = `<div style="font-weight:600;color:#6b7280;margin-bottom:8px;font-size:12px">${date}</div>`;
                let netFlow = 0;
                params.forEach(p => {
                    const val = Math.abs(p.data);
                    const color = p.seriesName === '主力流入' ? RISE_COLOR : FALL_COLOR;
                    const icon = p.seriesName === '主力流入' ? '↑' : '↓';
                    html += `<div style="display:flex;justify-content:space-between;gap:24px;margin-bottom:4px"><span style="color:${color}">${icon} ${p.seriesName}</span><span style="font-weight:600;color:#1f2937">${val.toFixed(2)}万</span></div>`;
                    if (p.seriesName === '主力流入') netFlow += val;
                    else netFlow -= val;
                });
                const netColor = netFlow >= 0 ? RISE_COLOR : FALL_COLOR;
                html += `<div style="display:flex;justify-content:space-between;gap:24px;padding-top:8px;border-top:1px dashed #e5e7eb;margin-top:4px"><span style="color:#6b7280">净流入</span><span style="font-weight:700;color:${netColor}">${netFlow >= 0 ? '+' : ''}${netFlow.toFixed(2)}万</span></div>`;
                return html;
            }
        },
        legend: { data: ['主力流入', '主力流出'] },
        grid: { left: '10%', right: '5%', bottom: '15%' },
        xAxis: { type: 'category', data: data.dates },
        yAxis: { type: 'value', axisLabel: { formatter: val => (val / 10000).toFixed(0) + '万' } },
        series: [
            {
                name: '主力流入',
                type: 'bar',
                stack: 'total',
                data: data.inflow,
                itemStyle: { color: RISE_COLOR }
            },
            {
                name: '主力流出',
                type: 'bar',
                stack: 'total',
                data: data.outflow.map(v => -v),
                itemStyle: { color: FALL_COLOR }
            }
        ]
    };
}

/**
 * 估值仪表盘配置
 */
function createValuationGaugeOption(value, label) {
    return {
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(255,255,255,0.98)',
            borderColor: '#e5e7eb',
            borderWidth: 1,
            padding: [10, 14],
            textStyle: { color: '#1f2937', fontSize: 13 },
            extraCssText: 'box-shadow: 0 8px 24px rgba(0,0,0,0.08); border-radius: 8px;',
            formatter: function(params) {
                const val = params.value;
                let status, color;
                if (val < 30) { status = '低估'; color = '#16a34a'; }
                else if (val < 70) { status = '合理'; color = '#ca8a04'; }
                else { status = '高估'; color = '#dc2626'; }
                return `<div style="text-align:center"><div style="font-size:12px;color:#6b7280;margin-bottom:4px">${label || '估值分位'}</div><div style="font-size:20px;font-weight:700;color:${color}">${val.toFixed(1)}%</div><div style="font-size:12px;color:${color};margin-top:4px">${status}</div></div>`;
            }
        },
        series: [{
            type: 'gauge',
            startAngle: 200,
            endAngle: -20,
            min: 0,
            max: 100,
            splitNumber: 10,
            axisLine: {
                lineStyle: {
                    width: 20,
                    color: [
                        [0.3, FALL_COLOR],
                        [0.7, '#f59e0b'],
                        [1, RISE_COLOR]
                    ]
                }
            },
            pointer: { itemStyle: { color: '#374151' } },
            axisTick: { distance: -20, length: 6, lineStyle: { color: '#fff', width: 1 } },
            splitLine: { distance: -22, length: 20, lineStyle: { color: '#fff', width: 2 } },
            axisLabel: { color: '#9ca3af', distance: 30, fontSize: 10 },
            detail: {
                valueAnimation: true,
                formatter: `{value}\n${label || ''}`,
                color: '#374151',
                fontSize: 16,
                offsetCenter: [0, '70%']
            },
            data: [{ value: value || 0 }]
        }]
    };
}

// 导出
window.Charts = {
    createKlineOption,
    createRadarOption,
    createCapitalFlowOption,
    createValuationGaugeOption,
    RISE_COLOR,
    FALL_COLOR
};
