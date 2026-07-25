/**
 * 自选股管理模块
 * 
 * 职责:
 * - 添加/移除自选股
 * - 检查某只股票是否在自选中
 * - 刷新自选股列表
 * - 在搜索结果和股票头部显示收藏状态
 */

// 自选股缓存（避免重复请求）
let watchlistCache = null;
let watchlistCacheTime = 0;
const CACHE_TTL = 60000; // 1分钟缓存

/**
 * 获取自选股列表
 * @param {boolean} forceRefresh - 是否强制刷新
 * @returns {Promise<Array>} 自选股代码数组
 */
async function getWatchlist(forceRefresh = false) {
    const now = Date.now();
    
    // 使用缓存
    if (!forceRefresh && watchlistCache && (now - watchlistCacheTime < CACHE_TTL)) {
        return watchlistCache;
    }
    
    try {
        const res = await fetch('/api/watchlist');
        const data = await res.json();
        
        if (data.watchlist && Array.isArray(data.watchlist)) {
            watchlistCache = data.watchlist.map(item => item.code);
            watchlistCacheTime = now;
            return watchlistCache;
        }
        
        return [];
    } catch (err) {
        console.error('[watchlist] 获取自选股列表失败:', err);
        return [];
    }
}

/**
 * 检查股票是否在自选中
 * @param {string} code - 股票代码
 * @returns {Promise<boolean>}
 */
async function isInWatchlist(code) {
    const list = await getWatchlist();
    return list.includes(code);
}

/**
 * 添加自选股
 * @param {string} code - 股票代码
 * @param {string} name - 股票名称
 * @returns {Promise<boolean>} 是否成功
 */
async function addToWatchlist(code, name = '') {
    try {
        const res = await fetch('/api/watchlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, name })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            // 清除缓存，下次请求时重新获取
            watchlistCache = null;
            showToast(data.message || '已添加自选股', 'success');
            return true;
        } else {
            showToast(data.error || '添加失败', 'error');
            return false;
        }
    } catch (err) {
        console.error('[watchlist] 添加自选股失败:', err);
        showToast('添加失败，请重试', 'error');
        return false;
    }
}

/**
 * 从自选股移除
 * @param {string} code - 股票代码
 * @param {HTMLElement} buttonEl - 按钮元素（用于动画）
 * @returns {Promise<boolean>}
 */
async function removeFromWatchlist(code, buttonEl = null) {
    // 确认删除
    if (!confirm('确定要移除该自选股吗？')) {
        return false;
    }
    
    try {
        const res = await fetch(`/api/watchlist/${code}`, {
            method: 'DELETE'
        });
        
        const data = await res.json();
        
        if (res.ok) {
            // 清除缓存
            watchlistCache = null;
            
            // 动画效果
            if (buttonEl) {
                const item = buttonEl.closest('.watchlist-item');
                if (item) {
                    item.style.transition = 'all 0.3s ease';
                    item.style.opacity = '0';
                    item.style.transform = 'translateX(20px)';
                    setTimeout(() => {
                        // 刷新列表
                        refreshWatchlistUI();
                    }, 300);
                }
            } else {
                refreshWatchlistUI();
            }
            
            showToast(data.message || '已移除自选股', 'success');
            return true;
        } else {
            showToast(data.error || '移除失败', 'error');
            return false;
        }
    } catch (err) {
        console.error('[watchlist] 移除自选股失败:', err);
        showToast('移除失败，请重试', 'error');
        return false;
    }
}

/**
 * 刷新自选股 UI（通过 HTMX 重新请求）
 */
function refreshWatchlistUI() {
    // 触发 HTMX 重新请求
    const containers = document.querySelectorAll('[hx-get="/api/watchlist"]');
    containers.forEach(container => {
        if (typeof htmx !== 'undefined') {
            htmx.trigger(container, 'htmx:load');
        }
    });
    
    // 更新收藏按钮状态
    updateWatchlistButtons();
}

/**
 * 更新页面上的收藏按钮状态
 */
async function updateWatchlistButtons() {
    const buttons = document.querySelectorAll('.watchlist-btn');
    if (buttons.length === 0) return;
    
    const list = await getWatchlist(true);
    
    buttons.forEach(btn => {
        const code = btn.dataset.code;
        const isInList = list.includes(code);
        
        if (isInList) {
            btn.classList.remove('text-gray-400', 'hover:text-yellow-500');
            btn.classList.add('text-yellow-500');
            btn.title = '取消自选';
            btn.innerHTML = `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
            </svg>`;
        } else {
            btn.classList.remove('text-yellow-500');
            btn.classList.add('text-gray-400', 'hover:text-yellow-500');
            btn.title = '添加自选';
            btn.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
            </svg>`;
        }
    });
}

/**
 * 简单的 Toast 提示
 * @param {string} message - 消息内容
 * @param {string} type - 类型：success/error/info
 */
function showToast(message, type = 'info') {
    // 移除已存在的 toast
    const existing = document.querySelector('.watchlist-toast');
    if (existing) existing.remove();
    
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500'
    };
    
    const toast = document.createElement('div');
    toast.className = `watchlist-toast fixed top-4 right-4 px-4 py-2 rounded-lg shadow-lg text-white text-sm z-50 transition-all duration-300 ${colors[type] || colors.info}`;
    toast.textContent = message;
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px)';
    
    document.body.appendChild(toast);
    
    // 显示动画
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
    });
    
    // 3秒后消失
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * 切换自选股状态
 * @param {string} code - 股票代码
 * @param {string} name - 股票名称
 * @param {HTMLElement} button - 按钮元素
 */
async function toggleWatchlist(code, name, button) {
    const isInList = await isInWatchlist(code);
    
    if (isInList) {
        // 移除自选
        await removeFromWatchlist(code, button);
    } else {
        // 添加自选
        const success = await addToWatchlist(code, name);
        if (success) {
            // 更新按钮状态
            if (button) {
                button.classList.remove('text-gray-400', 'hover:text-yellow-500');
                button.classList.add('text-yellow-500');
                button.title = '取消自选';
                button.innerHTML = `<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"/>
                </svg>`;
            }
        }
    }
}

// 全局暴露函数供 HTML 调用
window.addToWatchlist = addToWatchlist;
window.removeFromWatchlist = removeFromWatchlist;
window.updateWatchlistButtons = updateWatchlistButtons;
window.toggleWatchlist = toggleWatchlist;