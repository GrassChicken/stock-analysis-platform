/**
 * 综合评分 + 雷达图模块
 * 
 * 职责:
 * - 从 API 获取股票六维评分（基本面/技术面/估值面/资金面/行业面/成长性）
 * - 填充评分卡片（总分、评级、六维明细）
 * - 初始化 ECharts 雷达图
 * 
 * 依赖:
 * - window.STOCK_CODE (由 analysis.html 注入)
 * - echarts (CDN 引入)
 * - window.radarChart (全局雷达图实例，用于 resize)
 */

/**
 * 加载综合评分并渲染雷达图
 * 调用 /api/stock/<code>/score 接口
 */
async function loadScoreAndRadar() {
    try {
        const res = await fetch(`/api/stock/${STOCK_CODE}/score`);
        const data = await res.json();

        if (data && !data.error) {
            // 填充总分
            const score = data.total_score || 0;
            document.getElementById('total-score').textContent = score.toFixed(1);

            // 填充评级徽章
            const badge = document.getElementById('rating-badge');
            const rating = data.rating || '--';
            const ratingColors = {
                'A+': 'bg-green-100 text-green-700',
                'A':  'bg-blue-100 text-blue-700',
                'B':  'bg-yellow-100 text-yellow-700',
                'C':  'bg-gray-100 text-gray-500'
            };
            badge.textContent = `评级: ${rating}`;
            badge.className = `mt-2 inline-block px-3 py-1 rounded-full text-sm font-semibold ${ratingColors[rating] || 'bg-gray-100 text-gray-500'}`;

            // 填充六维评分明细（带淡入动画）
            const breakdown = document.getElementById('score-breakdown');
            if (data.breakdown) {
                const { fundamental_score, technical_score, valuation_score, capital_score, industry_score, growth_score } = data.breakdown;
                breakdown.innerHTML = `
                    <div class="text-xs text-gray-600 space-y-1">
                        <div class="flex justify-between fade-in"><span>基本面</span><span class="font-semibold">${fundamental_score?.toFixed(1) || '--'}</span></div>
                        <div class="flex justify-between fade-in" style="animation-delay: 0.1s"><span>技术面</span><span class="font-semibold">${technical_score?.toFixed(1) || '--'}</span></div>
                        <div class="flex justify-between fade-in" style="animation-delay: 0.2s"><span>估值面</span><span class="font-semibold">${valuation_score?.toFixed(1) || '--'}</span></div>
                        <div class="flex justify-between fade-in" style="animation-delay: 0.3s"><span>资金面</span><span class="font-semibold">${capital_score?.toFixed(1) || '--'}</span></div>
                        <div class="flex justify-between fade-in" style="animation-delay: 0.4s"><span>行业面</span><span class="font-semibold">${industry_score?.toFixed(1) || '--'}</span></div>
                        <div class="flex justify-between fade-in" style="animation-delay: 0.5s"><span>成长性</span><span class="font-semibold">${growth_score?.toFixed(1) || '--'}</span></div>
                    </div>
                `;
            }

            // 初始化雷达图
            // ★ 关键修复：先让容器可见，再初始化图表（同 K 线图修复）
            document.getElementById('score-skeleton').classList.add('hidden');
            document.getElementById('score-content').classList.remove('hidden');

            // 等 DOM 重绘后再初始化图表，确保容器已有正确宽高
            requestAnimationFrame(() => {
                initRadarChart(data);
                if (window.radarChart) window.radarChart.resize();
            });
        }
    } catch (err) {
        console.error('[score-radar] 加载综合评分失败:', err);
    }
}

/**
 * 初始化/更新 ECharts 雷达图
 * 核心: 使用 getInstanceByDom 防止重复创建实例导致内存泄漏
 * 
 * @param {Object} data - 评分数据，需包含 data.breakdown
 */
function initRadarChart(data) {
    if (!data || !data.breakdown) return;

    const dom = document.getElementById('radar-chart');
    // 获取已有实例或创建新实例
    window.radarChart = echarts.getInstanceByDom(dom) || echarts.init(dom);

    const { fundamental_score, technical_score, valuation_score, capital_score, industry_score } = data.breakdown;

    window.radarChart.setOption({
        radar: {
            center: ['50%', '50%'],   // 完全居中
            radius: '75%',            // 进一步增大尺寸
            indicator: [
                { name: '基本面', max: 100 },
                { name: '技术面', max: 100 },
                { name: '估值面', max: 100 },
                { name: '资金面', max: 100 },
                { name: '行业面', max: 100 }
            ],
            axisName: {
                color: '#666',
                fontSize: 13,
                fontWeight: 500
            },
            splitArea: {
                areaStyle: {
                    color: ['rgba(59, 130, 246, 0.05)', 'rgba(59, 130, 246, 0.1)']
                }
            },
            axisLine: {
                lineStyle: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            }
        },
        series: [{
            type: 'radar',
            data: [{
                value: [
                    fundamental_score || 0,
                    technical_score || 0,
                    valuation_score || 0,
                    capital_score || 0,
                    industry_score || 0
                ],
                name: '评分'
            }],
            itemStyle: {
                color: '#3b82f6'
            },
            areaStyle: {
                color: 'rgba(59, 130, 246, 0.2)'
            },
            lineStyle: {
                color: '#3b82f6',
                width: 2
            }
        }]
    });
}
