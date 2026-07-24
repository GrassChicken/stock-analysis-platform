/**
 * AI 智能分析渲染模块
 * 
 * 职责:
 * - 渲染 AI 分析按钮和加载状态
 * - 调用 AI 分析 API 获取深度分析结果
 * - 展示 AI 生成的投资建议
 * 
 * 依赖:
 * - window.STOCK_CODE (由 analysis.html 注入)
 */

/**
 * 渲染 AI 分析界面
 * @returns {string} HTML 字符串
 */
function renderAIAnalysis() {
    return `
    <div class="text-center py-12">
        <div class="mb-6">
            <div class="text-6xl mb-4">🤖</div>
            <h3 class="text-xl font-semibold text-gray-700 mb-2">AI 智能分析</h3>
            <p class="text-gray-500 text-sm mb-6">基于六维评分数据，AI 为您提供专业投资建议</p>
        </div>
        <button onclick="startAIAnalysis()" id="ai-analyze-btn" class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-8 py-3 rounded-lg font-medium hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl">
            开始 AI 分析
        </button>
        <div id="ai-loading" class="hidden mt-8">
            <div class="inline-block">
                <div class="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            </div>
            <p class="text-gray-600 mt-4 animate-pulse">AI 正在分析中，请稍候...</p>
        </div>
        <div id="ai-result" class="hidden mt-8 text-left max-w-4xl mx-auto"></div>
        <div id="ai-error" class="hidden mt-8 text-red-500"></div>
    </div>
    `;
}

/**
 * 启动 AI 分析
 * 调用 /api/stock/<code>/ai 接口，获取 AI 生成的深度分析报告
 */
async function startAIAnalysis() {
    const btn = document.getElementById('ai-analyze-btn');
    const loading = document.getElementById('ai-loading');
    const result = document.getElementById('ai-result');
    const error = document.getElementById('ai-error');
    
    btn.disabled = true;
    btn.classList.add('opacity-50', 'cursor-not-allowed');
    loading.classList.remove('hidden');
    result.classList.add('hidden');
    error.classList.add('hidden');
    
    try {
        const res = await fetch(`/api/stock/${STOCK_CODE}/ai`);
        const data = await res.json();
        
        if (data.success) {
            result.classList.remove('hidden');
            result.innerHTML = `
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <div class="prose prose-sm max-w-none">
                        ${data.analysis.replace(/\\n/g, '<br>')}
                    </div>
                    <div class="mt-6 pt-4 border-t border-gray-200">
                        <p class="text-xs text-gray-400">生成时间：${new Date().toLocaleString()}</p>
                    </div>
                </div>
            `;
        } else {
            error.classList.remove('hidden');
            error.textContent = '分析失败：' + (data.error || '未知错误');
        }
    } catch (err) {
        error.classList.remove('hidden');
        error.textContent = '网络错误：' + err.message;
    } finally {
        loading.classList.add('hidden');
        btn.disabled = false;
        btn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}
