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

// 分组筛选状态
let currentGroupFilter = null; // null 表示显示全部

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
        // 名称兑底：深度分析页按钮传空 name 时，从页面已渲染的股票名取（排除仍等于代码的初始占位）
        if (!name) {
            const el = document.getElementById('stock-name');
            const t = el ? el.textContent.trim() : '';
            if (t && t !== code) name = t;
        }
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

// ==================== 分组管理 ====================

/**
 * 初始化分组筛选 Tab
 */
async function initGroupTabs() {
    const tabsContainer = document.getElementById('group-tabs');
    if (!tabsContainer) return;
    
    try {
        // 获取分组列表
        const res = await fetch('/api/watchlist/groups');
        const data = await res.json();
        const groups = data.groups || [];
        
        // 获取自选股完整列表（含分组信息）
        const wlRes = await fetch('/api/watchlist');
        const wlData = await wlRes.json();
        const watchlist = wlData.watchlist || [];
        
        // 统计每个分组的数量
        const groupCounts = {};
        watchlist.forEach(item => {
            const g = item.group || '默认';
            groupCounts[g] = (groupCounts[g] || 0) + 1;
        });
        
        // 渲染 Tab
        let html = '';
        
        // 全部 Tab
        const totalCount = watchlist.length;
        html += `
            <button class="group-tab flex-shrink-0 px-3 py-1.5 rounded-full text-sm font-medium transition-all whitespace-nowrap
                ${!currentGroupFilter ? 'bg-primary-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}"
                onclick="filterByGroup(null)">
                全部 <span class="ml-1 text-xs opacity-75">${totalCount}</span>
            </button>
        `;
        
        // 各分组 Tab
        const displayGroups = ['重点关注', '长线持有', '短线观察', '默认'];
        // 加上其他可能存在的自定义分组
        groups.forEach(g => {
            if (!displayGroups.includes(g)) displayGroups.push(g);
        });
        
        const groupColors = {
            '重点关注': { active: 'bg-red-500 text-white', dot: 'bg-red-400' },
            '长线持有': { active: 'bg-blue-500 text-white', dot: 'bg-blue-400' },
            '短线观察': { active: 'bg-yellow-500 text-white', dot: 'bg-yellow-400' },
            '默认': { active: 'bg-gray-600 text-white', dot: 'bg-gray-400' },
        };
        
        displayGroups.forEach(group => {
            const count = groupCounts[group] || 0;
            if (count === 0 && group !== '重点关注' && group !== '长线持有' && group !== '短线观察' && group !== '默认') return;
            
            const colors = groupColors[group] || { active: 'bg-purple-500 text-white', dot: 'bg-purple-400' };
            const isActive = currentGroupFilter === group;
            
            html += `
                <button class="group-tab flex-shrink-0 px-3 py-1.5 rounded-full text-sm font-medium transition-all whitespace-nowrap
                    ${isActive ? colors.active + ' shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}"
                    onclick="filterByGroup('${group}')">
                    <span class="inline-block w-2 h-2 rounded-full ${colors.dot} mr-1.5"></span>${group} <span class="ml-1 text-xs opacity-75">${count}</span>
                </button>
            `;
        });
        
        tabsContainer.innerHTML = html;
        
    } catch (err) {
        console.error('[watchlist] 初始化分组 Tab 失败:', err);
    }
}

/**
 * 按分组筛选
 * @param {string|null} group - 分组名称，null 表示全部
 */
function filterByGroup(group) {
    currentGroupFilter = group;
    
    // 重新渲染 Tab 样式
    initGroupTabs();
    
    // 筛选显示
    const items = document.querySelectorAll('.watchlist-item');
    let visibleCount = 0;
    
    items.forEach(item => {
        const itemGroup = item.dataset.group || '默认';
        if (!group || itemGroup === group) {
            item.style.display = '';
            visibleCount++;
        } else {
            item.style.display = 'none';
        }
    });
    
    // 无结果显示
    const container = document.getElementById('watchlist-container');
    let emptyMsg = container.querySelector('.group-empty-msg');
    if (visibleCount === 0 && group) {
        if (!emptyMsg) {
            emptyMsg = document.createElement('div');
            emptyMsg.className = 'group-empty-msg text-center py-6';
            emptyMsg.innerHTML = `
                <p class="text-sm text-gray-400">「${group}」分组暂无股票</p>
                <p class="text-xs text-gray-300 mt-1">点击股票右侧的分组按钮移动到此分组</p>
            `;
            container.appendChild(emptyMsg);
        }
    } else if (emptyMsg) {
        emptyMsg.remove();
    }
}

/**
 * 切换分组下拉菜单
 */
function toggleGroupMenu(code, button) {
    // 关闭其他已打开的菜单
    document.querySelectorAll('.group-menu').forEach(menu => {
        if (!menu.closest('.group-move-btn').contains(button)) {
            menu.classList.add('hidden');
        }
    });
    
    // 切换当前菜单
    const menu = button.nextElementSibling;
    if (menu && menu.classList.contains('group-menu')) {
        menu.classList.toggle('hidden');
    }
}

/**
 * 移动股票到指定分组
 * @param {string} code - 股票代码
 * @param {string} groupName - 目标分组名
 */
async function moveToGroup(code, groupName) {
    try {
        const res = await fetch(`/api/watchlist/${code}/group`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ group: groupName })
        });
        
        const data = await res.json();
        
        if (res.ok) {
            // 关闭菜单
            document.querySelectorAll('.group-menu').forEach(menu => menu.classList.add('hidden'));
            
            // 更新 DOM 中的 data-group
            const item = document.querySelector(`.watchlist-item[data-code="${code}"]`);
            if (item) {
                item.dataset.group = groupName;
                
                // 更新分组标签样式（动态创建或更新 badge）
                const colorMap = {
                    '重点关注': 'bg-red-100 text-red-700',
                    '长线持有': 'bg-blue-100 text-blue-700',
                    '短线观察': 'bg-yellow-100 text-yellow-700',
                    '默认': 'bg-gray-100 text-gray-600'
                };
                const colorClass = colorMap[groupName] || 'bg-gray-100 text-gray-600';
                
                let badge = item.querySelector('span.inline-flex');
                if (badge) {
                    // 更新已有 badge
                    badge.className = badge.className.replace(/bg-\w+-100 text-\w+-700/g, '').trim();
                    badge.className += ' ' + colorClass;
                    badge.textContent = groupName;
                } else if (groupName !== '默认') {
                    // 动态创建 badge（初始是"默认"分组时不存在 badge 元素）
                    badge = document.createElement('span');
                    badge.className = `inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colorClass}`;
                    badge.textContent = groupName;
                    badge.style.transition = 'all 0.3s ease';
                    badge.style.transform = 'scale(0)';
                    badge.style.opacity = '0';
                    // 插入到股票代码后面
                    const codeSpan = item.querySelector('span.text-sm.text-gray-500');
                    if (codeSpan && codeSpan.parentNode) {
                        codeSpan.after(badge);
                    }
                    // 动画展开
                    requestAnimationFrame(() => {
                        badge.style.transform = 'scale(1.15)';
                        badge.style.opacity = '1';
                        setTimeout(() => { badge.style.transform = 'scale(1)'; }, 200);
                    });
                }
                
                // 缩放动画
                if (badge) {
                    badge.style.transition = 'all 0.3s ease';
                    badge.style.transform = 'scale(1.15)';
                    setTimeout(() => { badge.style.transform = 'scale(1)'; }, 300);
                }
            }
            
            // 刷新 Tab 计数
            initGroupTabs();
            
            // 如果当前有分组筛选，重新筛选
            if (currentGroupFilter) {
                filterByGroup(currentGroupFilter);
            }
            
            showToast(data.message || `已移动到「${groupName}」`, 'success');
        } else {
            showToast(data.error || '移动失败', 'error');
        }
    } catch (err) {
        console.error('[watchlist] 移动分组失败:', err);
        showToast('移动失败，请重试', 'error');
    }
}

// 点击页面空白处关闭分组菜单
document.addEventListener('click', function(e) {
    if (!e.target.closest('.group-move-btn')) {
        document.querySelectorAll('.group-menu').forEach(menu => menu.classList.add('hidden'));
    }
});

// 全局暴露函数供 HTML 调用
window.addToWatchlist = addToWatchlist;
window.removeFromWatchlist = removeFromWatchlist;
window.updateWatchlistButtons = updateWatchlistButtons;
window.toggleWatchlist = toggleWatchlist;
window.initGroupTabs = initGroupTabs;
window.filterByGroup = filterByGroup;
window.toggleGroupMenu = toggleGroupMenu;
window.moveToGroup = moveToGroup;