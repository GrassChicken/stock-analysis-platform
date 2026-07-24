/**
 * 股票头部信息模块
 * 
 * 职责:
 * - 从 API 获取股票实时行情（名称、行业、价格、涨跌幅）
 * - 填充头部信息区域
 * - 骨架屏加载完成后切换显示
 * 
 * 依赖:
 * - window.STOCK_CODE (由 analysis.html 注入)
 */

/**
 * 加载股票头部基本信息
 * 调用 /api/stock/<code>/quote 接口，填充股票名称、行业、价格、涨跌幅
 */
async function loadStockHeader() {
    try {
        const res = await fetch(`/api/stock/${STOCK_CODE}/quote`);
        const data = await res.json();

        if (data && !data.error) {
            // 填充基本信息
            document.getElementById('stock-name').textContent = `${data.name || ''} ${STOCK_CODE}`;
            document.getElementById('stock-industry').textContent = data.industry || '';
            document.getElementById('stock-price').textContent = data.price?.toFixed(2) || '--';
            document.getElementById('stock-change').textContent = data.change_pct?.toFixed(2) + '%' || '--';

            // 切换骨架屏 → 实际内容（统一使用 classList，与 Tailwind hidden 配合）
            document.getElementById('header-skeleton').classList.add('hidden');
            document.getElementById('stock-header').classList.remove('hidden');
        }
    } catch (err) {
        console.error('[stock-header] 加载股票基本信息失败:', err);
    }
}
