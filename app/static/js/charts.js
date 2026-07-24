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
            axisPointer: { type: 'cross' },
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderColor: '#e5e7eb',
            textStyle: { color: '#374151', fontSize: 12 }
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
        tooltip: {},
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
        tooltip: { trigger: 'axis' },
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
