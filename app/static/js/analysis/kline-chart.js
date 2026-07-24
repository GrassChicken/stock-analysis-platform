/**
 * K线图模块
 * 
 * 职责:
 * - 从 API 获取股票K线数据（日K/周K/月K）
 * - 初始化 ECharts K线图（含成交量、tooltip、dataZoom）
 * - 支持切换K线周期
 * - 显示数据截止时间提示
 * 
 * 依赖:
 * - window.STOCK_CODE (由 analysis.html 注入)
 * - echarts (CDN 引入)
 * - window.klineChart (全局K线图实例，用于 resize)
 */

/**
 * 加载K线数据并渲染图表
 * 
 * @param {string} period - K线周期：'daily' | 'weekly' | 'monthly'
 */
async function loadKline(period = 'daily') {
    try {
        const count = period === 'daily' ? 60 : 120;
        const res = await fetch(`/api/stock/${STOCK_CODE}/kline?period=${period}&count=${count}`);
        const data = await res.json();

        if (data && data.data && data.data.length > 0) {
            // 显示数据截止时间提示
            const lastTradeDate = data.data[data.data.length - 1].trade_date;
            const dateHint = document.getElementById('data-hint');
            if (lastTradeDate && dateHint) {
                const year = lastTradeDate.slice(0, 4);
                const month = parseInt(lastTradeDate.slice(4, 6));
                const day = parseInt(lastTradeDate.slice(6, 8));
                dateHint.textContent = `数据截止${year}-${month}-${day}，交易日数据在收盘后60分钟刷新！`;
            }

            // ★ 关键修复：先让容器可见，再初始化图表，避免 display:none 下 ECharts 获取宽度为 0
            document.getElementById('kline-skeleton').classList.add('hidden');
            document.getElementById('kline-content').classList.remove('hidden');

            // 等 DOM 重绘后再初始化图表，确保容器已有正确宽高
            requestAnimationFrame(() => {
                initKlineChart(data);
                // 额外保险：强制 resize
                if (window.klineChart) window.klineChart.resize();
            });
        }
    } catch (err) {
        console.error('[kline-chart] 加载K线数据失败:', err);
    }
}

/**
 * 初始化/更新 ECharts K线图（含成交量、tooltip、缩放）
 * 
 * @param {Object} klineData - K线数据，需包含 klineData.data 数组
 */
function initKlineChart(klineData) {
    if (!klineData || !klineData.data) return;

    const dom = document.getElementById('kline-chart');
    // 获取已有实例或创建新实例
    window.klineChart = echarts.getInstanceByDom(dom) || echarts.init(dom);

    // 准备数据
    const dates = klineData.data.map(item => item.trade_date);
    const values = klineData.data.map(item => [item.open, item.close, item.low, item.high]);
    const volumes = klineData.data.map((item, index) => {
        // 涨跌颜色：收盘>=开盘为涨（红），否则为跌（绿）
        const isUp = item.close >= item.open;
        return [index, item.vol || 0, isUp ? 1 : -1];
    });

    window.klineChart.setOption({
        // 全局 tooltip
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                lineStyle: { color: '#888', type: 'dashed' }
            },
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#ddd',
            borderWidth: 1,
            textStyle: { color: '#333', fontSize: 12 },
            formatter: function (params) {
                const dataIndex = params[0].dataIndex;
                const item = klineData.data[dataIndex];
                const change = item.close - item.open;
                const changePct = item.open > 0 ? (change / item.open * 100).toFixed(2) : 0;
                const color = change >= 0 ? '#ef4444' : '#22c55e';
                
                return `
                    <div style="font-weight:600;margin-bottom:6px;color:#666">${item.trade_date}</div>
                    <div style="display:grid;grid-template-columns:60px 1fr;gap:4px 8px;font-size:12px;line-height:1.6">
                        <span style="color:#888">开盘:</span><span>${item.open.toFixed(2)}</span>
                        <span style="color:#888">收盘:</span><span style="color:${color};font-weight:600">${item.close.toFixed(2)}</span>
                        <span style="color:#888">最高:</span><span>${item.high.toFixed(2)}</span>
                        <span style="color:#888">最低:</span><span>${item.low.toFixed(2)}</span>
                        <span style="color:#888">涨跌:</span><span style="color:${color}">${change.toFixed(2)} (${changePct}%)</span>
                        <span style="color:#888">成交量:</span><span>${(item.vol / 10000).toFixed(2)}万手</span>
                    </div>
                `;
            }
        },
        // 布局：K线图 + 成交量图 上下排列
        grid: [
            { left: 60, right: 20, top: 10, height: '55%' },    // K线区域
            { left: 60, right: 20, top: '70%', height: '20%' }  // 成交量区域
        ],
        // X轴（共享日期）
        xAxis: [
            {
                type: 'category',
                data: dates,
                gridIndex: 0,
                axisLabel: { show: false },  // K线图不显示日期，避免拥挤
                axisTick: { show: false }
            },
            {
                type: 'category',
                data: dates,
                gridIndex: 1,
                axisLabel: {
                    fontSize: 10,
                    color: '#888',
                    rotate: 30,
                    formatter: function(value) {
                        // 只显示月-日
                        return value.slice(4, 6) + '-' + value.slice(6, 8);
                    }
                },
                axisTick: { show: false }
            }
        ],
        // Y轴
        yAxis: [
            {
                scale: true,
                gridIndex: 0,
                splitLine: { lineStyle: { color: '#f0f0f0' } },
                axisLabel: { fontSize: 10, color: '#888' }
            },
            {
                scale: true,
                gridIndex: 1,
                splitLine: { show: false },
                axisLabel: {
                    fontSize: 10,
                    color: '#888',
                    formatter: function(value) {
                        return (value / 10000).toFixed(0) + '万';
                    }
                }
            }
        ],
        // 缩放组件
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0, 1],
                start: 0,
                end: 100
            },
            {
                type: 'slider',
                xAxisIndex: [0, 1],
                bottom: 5,
                height: 14,
                borderColor: 'transparent',
                backgroundColor: '#f5f5f5',
                fillerColor: 'rgba(59, 130, 246, 0.2)',
                handleStyle: { color: '#3b82f6' },
                textStyle: { color: '#888', fontSize: 10 }
            }
        ],
        // 数据系列
        series: [
            {
                type: 'candlestick',
                data: values,
                itemStyle: {
                    color: '#ef4444',          // 涨：红色
                    color0: '#22c55e',         // 跌：绿色
                    borderColor: '#ef4444',
                    borderColor0: '#22c55e'
                }
            },
            {
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: volumes.map(v => ({
                    value: v[1],
                    itemStyle: {
                        color: v[2] >= 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(34, 197, 94, 0.6)'
                    }
                }))
            }
        ]
    });
}
