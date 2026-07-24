<!-- 全局 JS -->
// Tab 切换通用函数
function switchTab(btn, contentId) {
    document.querySelectorAll('.tab-btn').forEach(b => {
        b.classList.remove('text-primary-600', 'border-b-2', 'border-primary-600');
        b.classList.add('text-gray-500');
    });
    btn.classList.add('text-primary-600', 'border-b-2', 'border-primary-600');
    btn.classList.remove('text-gray-500');
}

// 数字滚动动画
function animateNumber(element, target, duration = 1000) {
    const start = 0;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (target - start) * easeOut);
        element.textContent = current;
        if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
}

// 格式化数字 (千分位)
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// 格式化金额 (亿/万)
function formatMoney(num) {
    if (num >= 1e8) return (num / 1e8).toFixed(2) + '亿';
    if (num >= 1e4) return (num / 1e4).toFixed(2) + '万';
    return num.toFixed(2);
}

// HTMX 事件监听
document.body.addEventListener('htmx:afterSwap', function(evt) {
    // 图表重新初始化 (如果需要)
    if (evt.detail.target.id === 'tab-content') {
        window.dispatchEvent(new Event('resize'));
    }
});

console.log('✅ 智能股票深度分析平台 - 前端就绪');
