/**
 * Tab 内容加载调度器
 * 
 * 职责:
 * - 根据当前激活的 Tab 名称，调用对应 API 获取数据
 * - 分发给对应的 render 函数渲染
 * - 管理骨架屏显隐
 * 
 * 依赖:
 * - window.STOCK_CODE (由 analysis.html 注入)
 * - 各 tab 渲染函数 (renderFundamental, renderTechnical 等，由对应 js 文件提供)
 */

/**
 * 加载指定 Tab 的内容
 * @param {string} tab - Tab 标识：fundamental|technical|valuation|dupont|capital|industry|ai
 */
async function loadTabContent(tab) {
    const skeleton = document.getElementById('tab-skeleton');
    const body = document.getElementById('tab-body');
    if (skeleton) skeleton.classList.remove('hidden');
    if (body) body.classList.add('hidden');

    try {
        let html = '';
        if (tab === 'fundamental') {
            const res = await fetch(`/api/stock/${STOCK_CODE}/fundamental`);
            const data = await res.json();
            html = renderFundamental(data);
        } else if (tab === 'valuation') {
            const res = await fetch(`/api/stock/${STOCK_CODE}/valuation`);
            const data = await res.json();
            html = renderValuation(data);
        } else if (tab === 'dupont') {
            const res = await fetch(`/api/stock/${STOCK_CODE}/dupont`);
            const data = await res.json();
            html = renderDupont(data);
        } else if (tab === 'technical') {
            const res = await fetch(`/api/stock/${STOCK_CODE}/technical`);
            const data = await res.json();
            html = renderTechnical(data);
        } else if (tab === 'capital') {
            const res = await fetch(`/api/stock/${STOCK_CODE}/capital`);
            const data = await res.json();
            html = renderCapital(data);
        } else if (tab === 'industry') {
            const res = await fetch(`/api/stock/${STOCK_CODE}/industry`);
            const data = await res.json();
            html = renderIndustry(data);
        } else if (tab === 'ai') {
            html = renderAIAnalysis();
        }
        body.innerHTML = `<div class="tab-transition">${html}</div>`;
    } catch (err) {
        body.innerHTML = `<div class="text-center py-8 text-red-500">加载失败: ${err.message}</div>`;
    }

    if (skeleton) skeleton.classList.add('hidden');
    if (body) body.classList.remove('hidden');
}
