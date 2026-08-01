/**
 * 券商金股池渲染模块
 * 
 * 职责:
 * - 渲染券商金股列表
 * - 显示共识度排行
 * - 支持月份切换
 */

let currentMonth = '';
let brokerData = null;

// 完整金股列表分页与搜索
let allStockData = [];
let filteredStockData = [];
let currentPage = 1;
const pageSize = 50;

/**
 * 初始化金股池页面
 */
async function initBrokerPage() {
    // 默认当前月
    const now = new Date();
    currentMonth = now.getFullYear() + String(now.getMonth() + 1).padStart(2, '0');
    
    // 更新月份选择器
    document.getElementById('month-input').value = currentMonth.substring(0, 4) + '-' + currentMonth.substring(4);
    
    await loadBrokerData();
}

/**
 * 加载券商金股数据
 */
async function loadBrokerData() {
    try {
        const response = await fetch(`/api/market/broker_recommend?month=${currentMonth}`);
        const data = await response.json();
        
        brokerData = data;
        renderBrokerPage();
    } catch (error) {
        console.error('加载券商金股失败:', error);
        document.getElementById('broker-content').innerHTML = '<div class="text-center py-8 text-red-500">加载失败，请稍后重试</div>';
    }
}

/**
 * 渲染金股池页面
 */
function renderBrokerPage() {
    if (!brokerData || !brokerData.available) {
        document.getElementById('broker-content').innerHTML = '<div class="text-center py-8 text-gray-400">暂无该月金股数据</div>';
        return;
    }
    
    const { consensus, data, month } = brokerData;
    
    let html = `
        <!-- 共识度排行 -->
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">🏆 券商共识度排行 TOP 10</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-4 py-3 text-left">排名</th>
                            <th class="px-4 py-3 text-left">股票</th>
                            <th class="px-4 py-3 text-center">推荐券商数</th>
                            <th class="px-4 py-3 text-left">推荐券商</th>
                            <th class="px-4 py-3 text-center">操作</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200">
    `;
    
    consensus.slice(0, 10).forEach((item, index) => {
        const brokersText = item.brokers.join('、');
        html += `
            <tr class="hover:bg-gray-50">
                <td class="px-4 py-3">
                    <span class="inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-semibold ${index < 3 ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}">${index + 1}</span>
                </td>
                <td class="px-4 py-3">
                    <div class="font-medium">${item.name || '--'}</div>
                    <div class="text-xs text-gray-500">${item.ts_code}</div>
                </td>
                <td class="px-4 py-3 text-center">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        ${item.count} 家
                    </span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-600">
                    <div class="max-w-xs truncate" title="${brokersText}">${brokersText}</div>
                </td>
                <td class="px-4 py-3 text-center">
                    <a href="/stock/${item.ts_code.split('.')[0]}" class="text-blue-600 hover:text-blue-800 text-xs">查看详情 →</a>
                </td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- 完整金股列表 -->
        <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-xl font-semibold mb-4">📋 完整金股列表</h2>
            <div class="text-sm text-gray-500 mb-3">共 ${data.length} 条推荐，来自 ${new Set(data.map(d => d.broker)).size} 家券商</div>
            
            <!-- 搜索框 -->
            <div class="mb-4 flex items-center">
                <input id="stock-search" type="text" placeholder="搜索股票名称、代码或券商..."
                    class="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
                <span class="ml-3 text-sm text-gray-500" id="stock-filter-info"></span>
            </div>
            
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead class="bg-gray-50">
                        <tr>
                            <th class="px-4 py-3 text-left">股票</th>
                            <th class="px-4 py-3 text-left">推荐券商</th>
                            <th class="px-4 py-3 text-center">操作</th>
                        </tr>
                    </thead>
                    <tbody id="stock-list-body" class="divide-y divide-gray-200">
    `;
    
    // 存储数据到全局变量，供分页和搜索使用
    allStockData = data;
    filteredStockData = data;
    currentPage = 1;
    
    html += `
                    </tbody>
                </table>
            </div>
            <!-- 分页 -->
            <div class="mt-4 flex items-center justify-between text-sm text-gray-600">
                <span id="stock-page-info"></span>
                <div class="flex items-center space-x-2">
                    <button id="stock-page-prev" class="px-3 py-1 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed" disabled>上一页</button>
                    <span id="stock-page-num"></span>
                    <button id="stock-page-next" class="px-3 py-1 border border-gray-200 rounded hover:bg-gray-50">下一页</button>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('broker-content').innerHTML = html;
    
    // 渲染当前页数据并绑定事件
    renderStockListPage();
    bindStockListEvents();
}

function renderStockListPage() {
    const tbody = document.getElementById('stock-list-body');
    if (!tbody) return;
    const total = filteredStockData.length;
    const totalPages = Math.max(1, Math.ceil(total / pageSize));
    if (currentPage > totalPages) currentPage = totalPages;
    const start = (currentPage - 1) * pageSize;
    const end = Math.min(start + pageSize, total);
    const pageData = filteredStockData.slice(start, end);
    
    tbody.innerHTML = pageData.map(item => `
        <tr class="hover:bg-gray-50">
            <td class="px-4 py-3">
                <div class="font-medium">${item.name || '--'}</div>
                <div class="text-xs text-gray-500">${item.ts_code}</div>
            </td>
            <td class="px-4 py-3 text-sm text-gray-600">${item.broker}</td>
            <td class="px-4 py-3 text-center">
                <a href="/stock/${item.ts_code.split('.')[0]}" class="text-blue-600 hover:text-blue-800 text-xs">查看详情 →</a>
            </td>
        </tr>
    `).join('');
    
    const pageInfo = document.getElementById('stock-page-info');
    const pageNum = document.getElementById('stock-page-num');
    const filterInfo = document.getElementById('stock-filter-info');
    const prevBtn = document.getElementById('stock-page-prev');
    const nextBtn = document.getElementById('stock-page-next');
    
    if (total === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="px-4 py-8 text-center text-gray-400 text-sm">未找到匹配结果</td></tr>';
        pageInfo.textContent = '共 0 条';
        pageNum.textContent = '0 / 0';
    } else {
        pageInfo.textContent = `第 ${start + 1}-${end} 条，共 ${total} 条`;
        pageNum.textContent = `${currentPage} / ${totalPages}`;
    }
    if (filterInfo) {
        filterInfo.textContent = filteredStockData.length === allStockData.length ? '' : `筛选出 ${filteredStockData.length} / ${allStockData.length} 条`;
    }
    
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
}

function bindStockListEvents() {
    const searchInput = document.getElementById('stock-search');
    const prevBtn = document.getElementById('stock-page-prev');
    const nextBtn = document.getElementById('stock-page-next');
    if (!searchInput || !prevBtn || !nextBtn) return;
    
    let searchTimer = null;
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            const kw = searchInput.value.trim().toLowerCase();
            if (!kw) {
                filteredStockData = allStockData;
            } else {
                filteredStockData = allStockData.filter(item => {
                    return (item.name && item.name.toLowerCase().includes(kw))
                        || (item.ts_code && item.ts_code.toLowerCase().includes(kw))
                        || (item.broker && item.broker.toLowerCase().includes(kw));
                });
            }
            currentPage = 1;
            renderStockListPage();
        }, 200);
    });
    
    prevBtn.addEventListener('click', () => { if (currentPage > 1) { currentPage--; renderStockListPage(); } });
    nextBtn.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredStockData.length / pageSize);
        if (currentPage < totalPages) { currentPage++; renderStockListPage(); }
    });
}

/**
 * 切换月份
 */
function changeMonth() {
    const monthInput = document.getElementById('month-input').value;
    if (!monthInput) {
        alert('请选择月份');
        return;
    }
    
    currentMonth = monthInput.replace('-', '');
    loadBrokerData();
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initBrokerPage);
