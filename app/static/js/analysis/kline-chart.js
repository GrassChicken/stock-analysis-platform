/**
 * K线图模块
 * 
 * 职责:
 * - 从 API 获取股票K线数据（日K/周K/月K）
 * - 初始化 ECharts K线图
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

            // 初始化K线图
            initKlineChart(data);

            // 切换骨架屏 → 实际内容（统一使用 classList）
            document.getElementById('kline-skeleton').classList.add('hidden');
            document.getElementById('kline-content').classList.remove('hidden');
        }
    } catch (err) {
        console.error('[kline-chart] 加载K线数据失败:', err);
    }
}

/**
 * 初始化/更新 ECharts K线图
 * 核心: 使用 getInstanceByDom 防止重复创建实例
 * 
 * @param {Object} klineData - K线数据，需包含 klineData.data 数组
 */
function initKlineChart(klineData) {
    if (!klineData || !klineData.data) return;

    const dom = document.getElementById('kline-chart');
    // 获取已有实例或创建新实例
    window.klineChart = echarts.getInstanceByDom(dom) || echarts.init(dom);

    const dates = klineData.data.map(item => item.trade_date);
    const values = klineData.data.map(item => [item.open, item.close, item.low, item.high]);

    window.klineChart.setOption({
        xAxis: { type: 'category', data: dates },
        yAxis: { scale: true },
        series: [{
            type: 'candlestick',
            data: values
        }]
    });
}
