/**
 * 股票分析页入口脚本
 * 
 * 职责:
 * - DOMContentLoaded 后初始化各模块加载
 * - 绑定 Tab 切换事件
 * - 绑定 K线周期切换事件（事件委托）
 * - 窗口 resize 时图表自适应
 * 
 * 依赖:
 * - window.STOCK_CODE (由 analysis.html 注入)
 * - loadStockHeader (stock-header.js)
 * - loadScoreAndRadar (score-radar.js)
 * - loadKline (kline-chart.js)
 * - loadTabContent (analysis-tabs.js)
 */

let radarChart = null;
let klineChart = null;

document.addEventListener('DOMContentLoaded', function() {
    // 异步加载各个模块
    loadStockHeader();
    loadScoreAndRadar();
    loadKline();

    // Tab 切换
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('text-primary-600', 'border-b-2', 'border-primary-600');
                b.classList.add('text-gray-500');
            });
            this.classList.add('text-primary-600', 'border-b-2', 'border-primary-600');
            this.classList.remove('text-gray-500');
            loadTabContent(this.dataset.tab);
        });
    });

    // K线周期切换（事件委托）
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('kline-period')) {
            document.querySelectorAll('.kline-period').forEach(b => {
                b.classList.remove('bg-primary-500', 'text-white');
                b.classList.add('bg-gray-100', 'text-gray-600');
            });
            e.target.classList.add('bg-primary-500', 'text-white');
            e.target.classList.remove('bg-gray-100', 'text-gray-600');
            loadKline(e.target.dataset.period);
        }
    });

    // 窗口 resize 时，图表自适应
    window.addEventListener('resize', function() {
        if (radarChart) radarChart.resize();
        if (klineChart) klineChart.resize();
    });
});
