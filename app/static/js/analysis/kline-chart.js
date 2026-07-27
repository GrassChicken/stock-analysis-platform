/**
 * K线图模块
 * 
 * 职责:
 * - 从 API 获取股票K线数据（日K/周K/月K）
 * - 初始化 ECharts K线图（含成交量、技术指标）
 * - 支持切换K线周期和技术指标
 * - 主图指标：MA均线（5/10/20/60）、BOLL布林带
 * - 副图指标：成交量、MACD、KDJ、RSI
 * 
 * 依赖:
 * - window.STOCK_CODE (由 analysis.html 注入)
 * - echarts (CDN 引入)
 * - window.klineChart (全局K线图实例，用于 resize)
 */

// 全局状态
let klineDataCache = null;
let activeMA = new Set([5, 10, 20]); // 默认显示MA5/10/20
let activeBOLL = false;
let activeSubIndicator = 'volume'; // 默认副图：成交量

/**
 * 计算移动平均线
 */
function calculateMA(data, period) {
    const result = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            result.push(null);
        } else {
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += data[i - j].close;
            }
            result.push(+(sum / period).toFixed(2));  // 返回数字
        }
    }
    return result;
}

/**
 * 计算布林带
 */
function calculateBOLL(data, period = 20, multiplier = 2) {
    const mid = [];
    const upper = [];
    const lower = [];
    
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            mid.push(null);
            upper.push(null);
            lower.push(null);
        } else {
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += data[i - j].close;
            }
            const ma = sum / period;
            
            let variance = 0;
            for (let j = 0; j < period; j++) {
                variance += Math.pow(data[i - j].close - ma, 2);
            }
            const std = Math.sqrt(variance / period);
            
            mid.push(+ma.toFixed(2));
            upper.push(+(ma + multiplier * std).toFixed(2));
            lower.push(+(ma - multiplier * std).toFixed(2));
        }
    }
    
    return { mid, upper, lower };
}

/**
 * 计算MACD
 */
function calculateMACD(data, shortPeriod = 12, longPeriod = 26, signalPeriod = 9) {
    const dif = [];
    const dea = [];
    const macd = [];
    
    let shortEMA = 0;
    let longEMA = 0;
    let prevDEA = 0;
    
    for (let i = 0; i < data.length; i++) {
        const close = data[i].close;
        
        if (i === 0) {
            shortEMA = close;
            longEMA = close;
            dif.push(0);
            dea.push(0);
            macd.push(0);
        } else {
            shortEMA = (close * 2 / (shortPeriod + 1)) + (shortEMA * (shortPeriod - 1) / (shortPeriod + 1));
            longEMA = (close * 2 / (longPeriod + 1)) + (longEMA * (longPeriod - 1) / (longPeriod + 1));
            
            const currentDIF = shortEMA - longEMA;
            const currentDEA = (currentDIF * 2 / (signalPeriod + 1)) + (prevDEA * (signalPeriod - 1) / (signalPeriod + 1));
            const currentMACD = (currentDIF - currentDEA) * 2;
            
            dif.push(+currentDIF.toFixed(3));   // 返回数字
            dea.push(+currentDEA.toFixed(3));
            macd.push(+currentMACD.toFixed(3));
            
            prevDEA = currentDEA;
        }
    }
    
    return { dif, dea, macd };
}

/**
 * 计算KDJ
 */
function calculateKDJ(data, n = 9, m1 = 3, m2 = 3) {
    const kArr = [];
    const dArr = [];
    const jArr = [];
    
    let prevK = 50;
    let prevD = 50;
    
    for (let i = 0; i < data.length; i++) {
        if (i < n - 1) {
            kArr.push(null);
            dArr.push(null);
            jArr.push(null);
        } else {
            let highest = -Infinity;
            let lowest = Infinity;
            
            for (let idx = 0; idx < n; idx++) {
                highest = Math.max(highest, +data[i - idx].high);
                lowest = Math.min(lowest, +data[i - idx].low);
            }
            
            const close = +data[i].close;
            const rsv = highest === lowest ? 50 : ((close - lowest) / (highest - lowest)) * 100;
            const currentK = (rsv * 2 / m1) + (prevK * (m1 - 1) / m1);
            const currentD = (currentK * 2 / m2) + (prevD * (m2 - 1) / m2);
            const currentJ = 3 * currentK - 2 * currentD;
            
            kArr.push(+currentK.toFixed(2));   // 返回数字
            dArr.push(+currentD.toFixed(2));
            jArr.push(+currentJ.toFixed(2));
            
            prevK = currentK;
            prevD = currentD;
        }
    }
    
    return { k: kArr, d: dArr, j: jArr };
}

/**
 * 计算RSI
 */
function calculateRSI(data, period = 14) {
    const rsi = [];
    let avgGain = 0;
    let avgLoss = 0;
    
    for (let i = 0; i < data.length; i++) {
        if (i === 0) {
            rsi.push(null);
            continue;
        }
        
        const change = +data[i].close - +data[i - 1].close;  // 确保数字运算
        const gain = change > 0 ? change : 0;
        const loss = change < 0 ? -change : 0;
        
        if (i <= period) {
            // 累积阶段：简单平均
            avgGain += gain;
            avgLoss += loss;
            
            if (i === period) {
                avgGain = avgGain / period;
                avgLoss = avgLoss / period;
                const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
                rsi.push(+(100 - 100 / (1 + rs)).toFixed(2));  // 返回数字
            } else {
                rsi.push(null);
            }
        } else {
            // Wilder平滑阶段
            avgGain = (avgGain * (period - 1) + gain) / period;
            avgLoss = (avgLoss * (period - 1) + loss) / period;
            const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
            rsi.push(+(100 - 100 / (1 + rs)).toFixed(2));
        }
    }
    
    return rsi;
}

/**
 * 加载K线数据并渲染图表
 * 
 * @param {string} period - K线周期：'daily' | 'weekly' | 'monthly'
 */
async function loadKline(period = 'daily') {
    try {
        const count = period === 'daily' ? 120 : 150; // 增加数据量以支持更多指标计算
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

            // 缓存数据
            klineDataCache = data;

            // ★ 关键修复：先让容器可见，再初始化图表，避免 display:none 下 ECharts 获取宽度为 0
            document.getElementById('kline-skeleton').classList.add('hidden');
            document.getElementById('kline-content').classList.remove('hidden');

            // 等 DOM 重绘后再初始化图表，确保容器已有正确宽高
            requestAnimationFrame(() => {
                initKlineChart(data);
                // 额外保险：强制 resize
                if (window.klineChart) window.klineChart.resize();
            });
        }
    } catch (err) {
        console.error('[kline-chart] 加载K线数据失败:', err);
    }
}

/**
 * 初始化/更新 ECharts K线图
 */
function initKlineChart(klineData) {
    if (!klineData || !klineData.data) return;

    const dom = document.getElementById('kline-chart');
    window.klineChart = echarts.getInstanceByDom(dom) || echarts.init(dom);

    // 准备数据
    const dates = klineData.data.map(item => item.trade_date);
    const values = klineData.data.map(item => [item.open, item.close, item.low, item.high]);
    const volumes = klineData.data.map((item, index) => {
        const isUp = item.close >= item.open;
        return [index, item.vol || 0, isUp ? 1 : -1];
    });

    // 计算技术指标
    const maData = {};
    activeMA.forEach(period => {
        maData[period] = calculateMA(klineData.data, period);
    });

    // 构建配置
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross',
                lineStyle: { color: '#888', type: 'dashed' }
            },
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#ddd',
            borderWidth: 1,
            textStyle: { color: '#333', fontSize: 12 }
        },
        legend: {
            data: [],
            top: 5,
            textStyle: { fontSize: 10 }
        },
        grid: [
            { left: 60, right: 20, top: 40, height: '50%' }
        ],
        xAxis: [
            {
                type: 'category',
                data: dates,
                gridIndex: 0,
                axisLabel: {
                    fontSize: 10,
                    color: '#888',
                    rotate: 30,
                    formatter: function(value) {
                        return value.slice(4, 6) + '-' + value.slice(6, 8);
                    }
                },
                axisTick: { show: false }
            }
        ],
        yAxis: [
            {
                scale: true,
                gridIndex: 0,
                splitLine: { lineStyle: { color: '#f0f0f0' } },
                axisLabel: { fontSize: 10, color: '#888' }
            }
        ],
        dataZoom: [
            {
                type: 'inside',
                xAxisIndex: [0],
                start: 50,
                end: 100
            },
            {
                type: 'slider',
                xAxisIndex: [0],
                bottom: 5,
                height: 14,
                borderColor: 'transparent',
                backgroundColor: '#f5f5f5',
                fillerColor: 'rgba(59, 130, 246, 0.2)',
                handleStyle: { color: '#3b82f6' },
                textStyle: { color: '#888', fontSize: 10 }
            }
        ],
        series: [
            {
                name: 'K线',
                type: 'candlestick',
                data: values,
                itemStyle: {
                    color: '#ef4444',
                    color0: '#22c55e',
                    borderColor: '#ef4444',
                    borderColor0: '#22c55e'
                }
            }
        ]
    };

    // 添加MA均线
    const maColors = { 5: '#f59e0b', 10: '#3b82f6', 20: '#8b5cf6', 60: '#ef4444' };
    activeMA.forEach(period => {
        option.legend.data.push(`MA${period}`);
        option.series.push({
            name: `MA${period}`,
            type: 'line',
            data: maData[period],
            smooth: true,
            lineStyle: { width: 1, color: maColors[period] },
            symbol: 'none',
            xAxisIndex: 0,
            yAxisIndex: 0
        });
    });

    // 添加BOLL布林带
    if (activeBOLL) {
        const boll = calculateBOLL(klineData.data);
        option.legend.data.push('BOLL中轨', 'BOLL上轨', 'BOLL下轨');
        option.series.push(
            {
                name: 'BOLL中轨',
                type: 'line',
                data: boll.mid,
                smooth: true,
                lineStyle: { width: 1, color: '#f59e0b' },
                symbol: 'none',
                xAxisIndex: 0,
                yAxisIndex: 0
            },
            {
                name: 'BOLL上轨',
                type: 'line',
                data: boll.upper,
                smooth: true,
                lineStyle: { width: 1, color: '#ef4444', type: 'dashed' },
                symbol: 'none',
                xAxisIndex: 0,
                yAxisIndex: 0
            },
            {
                name: 'BOLL下轨',
                type: 'line',
                data: boll.lower,
                smooth: true,
                lineStyle: { width: 1, color: '#22c55e', type: 'dashed' },
                symbol: 'none',
                xAxisIndex: 0,
                yAxisIndex: 0
            }
        );
    }

    // 根据副图指标调整布局
    if (activeSubIndicator === 'volume') {
        // 成交量副图
        option.grid.push({ left: 60, right: 20, top: '72%', height: '18%' });
        option.xAxis.push({
            type: 'category',
            data: dates,
            gridIndex: 1,
            axisLabel: { show: false },
            axisTick: { show: false }
        });
        option.yAxis.push({
            scale: true,
            gridIndex: 1,
            splitLine: { show: false },
            axisLabel: {
                fontSize: 10,
                color: '#888',
                formatter: function(value) {
                    return (value / 10000).toFixed(0) + '万';
                }
            }
        });
        option.series.push({
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes.map(v => ({
                value: v[1],
                itemStyle: {
                    color: v[2] >= 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(34, 197, 94, 0.6)'
                }
            }))
        });
    } else if (activeSubIndicator === 'macd') {
        // MACD副图
        const macd = calculateMACD(klineData.data);
        option.grid.push({ left: 60, right: 20, top: '72%', height: '18%' });
        option.xAxis.push({
            type: 'category',
            data: dates,
            gridIndex: 1,
            axisLabel: { show: false },
            axisTick: { show: false }
        });
        option.yAxis.push({
            scale: true,
            gridIndex: 1,
            splitLine: { lineStyle: { color: '#f0f0f0' } },
            axisLabel: {
                fontSize: 10,
                color: '#888',
                formatter: function(value) {
                    return value.toFixed(2);
                }
            }
        });
        // 添加MACD零轴参考线
        option.series.push({
            name: '_macd_zero',
            type: 'line',
            data: dates.map(() => 0),
            lineStyle: { width: 1, color: '#999', type: 'solid' },
            symbol: 'none',
            xAxisIndex: 1,
            yAxisIndex: 1,
            silent: true
        });
        option.legend.data.push('DIF', 'DEA', 'MACD');
        option.series.push(
            {
                name: 'DIF',
                type: 'line',
                data: macd.dif,
                smooth: true,
                lineStyle: { width: 1, color: '#3b82f6' },
                symbol: 'none',
                xAxisIndex: 1,
                yAxisIndex: 1
            },
            {
                name: 'DEA',
                type: 'line',
                data: macd.dea,
                smooth: true,
                lineStyle: { width: 1, color: '#f59e0b' },
                symbol: 'none',
                xAxisIndex: 1,
                yAxisIndex: 1
            },
            {
                name: 'MACD',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: macd.macd.map(v => ({
                    value: v,
                    itemStyle: {
                        color: v >= 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(34, 197, 94, 0.6)'
                    }
                }))
            }
        );
    } else if (activeSubIndicator === 'kdj') {
        // KDJ副图
        const kdj = calculateKDJ(klineData.data);
        option.grid.push({ left: 60, right: 20, top: '72%', height: '18%' });
        option.xAxis.push({
            type: 'category',
            data: dates,
            gridIndex: 1,
            axisLabel: { show: false },
            axisTick: { show: false }
        });
        option.yAxis.push({
            scale: true,   // 自适应范围，J值可能超过0-100
            gridIndex: 1,
            splitLine: { lineStyle: { color: '#f0f0f0' } },
            axisLabel: { fontSize: 10, color: '#888' }
        });
        // 添加KDJ参考线（20/50/80）
        option.series.push(
            {
                name: '_kdj_20',
                type: 'line',
                data: dates.map(() => 20),
                lineStyle: { width: 1, color: '#ccc', type: 'dashed' },
                symbol: 'none',
                xAxisIndex: 1,
                yAxisIndex: 1,
                silent: true
            },
            {
                name: '_kdj_80',
                type: 'line',
                data: dates.map(() => 80),
                lineStyle: { width: 1, color: '#ccc', type: 'dashed' },
                symbol: 'none',
                xAxisIndex: 1,
                yAxisIndex: 1,
                silent: true
            }
        );
        option.legend.data.push('K', 'D', 'J');
        option.series.push(
            {
                name: 'K',
                type: 'line',
                data: kdj.k,
                smooth: true,
                lineStyle: { width: 1, color: '#3b82f6' },
                symbol: 'none',
                xAxisIndex: 1,
                yAxisIndex: 1
            },
            {
                name: 'D',
                type: 'line',
                data: kdj.d,
                smooth: true,
                lineStyle: { width: 1, color: '#f59e0b' },
                symbol: 'none',
                xAxisIndex: 1,
                yAxisIndex: 1
            },
            {
                name: 'J',
                type: 'line',
                data: kdj.j,
                smooth: true,
                lineStyle: { width: 1, color: '#8b5cf6' },
                symbol: 'none',
                xAxisIndex: 1,
                yAxisIndex: 1
            }
        );
    } else if (activeSubIndicator === 'rsi') {
        // RSI副图
        const rsi = calculateRSI(klineData.data);
        option.grid.push({ left: 60, right: 20, top: '72%', height: '18%' });
        option.xAxis.push({
            type: 'category',
            data: dates,
            gridIndex: 1,
            axisLabel: { show: false },
            axisTick: { show: false }
        });
        option.yAxis.push({
            min: 0,
            max: 100,
            interval: 20,
            gridIndex: 1,
            splitLine: { lineStyle: { color: '#f0f0f0' } },
            axisLabel: { fontSize: 10, color: '#888' }
        });
        // 添加RSI参考线（30/70）
        option.series.push(
            {
                name: '_rsi_30',
                type: 'line',
                data: dates.map(() => 30),
                lineStyle: { width: 1, color: '#22c55e', type: 'dashed' },
                symbol: 'none',
                xAxisIndex: 1,
                yAxisIndex: 1,
                silent: true
            },
            {
                name: '_rsi_70',
                type: 'line',
                data: dates.map(() => 70),
                lineStyle: { width: 1, color: '#ef4444', type: 'dashed' },
                symbol: 'none',
                xAxisIndex: 1,
                yAxisIndex: 1,
                silent: true
            }
        );
        option.legend.data.push('RSI');
        option.series.push({
            name: 'RSI',
            type: 'line',
            data: rsi,
            smooth: true,
            lineStyle: { width: 1, color: '#8b5cf6' },
            symbol: 'none',
            xAxisIndex: 1,
            yAxisIndex: 1
        });
    }

    window.klineChart.setOption(option, { notMerge: true });
}

// 初始化事件监听
document.addEventListener('DOMContentLoaded', function() {
    // MA均线切换
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('ma-toggle')) {
            const period = parseInt(e.target.dataset.ma);
            if (activeMA.has(period)) {
                activeMA.delete(period);
                e.target.classList.remove('bg-primary-500', 'text-white');
                e.target.classList.add('bg-gray-100', 'text-gray-600');
            } else {
                activeMA.add(period);
                e.target.classList.add('bg-primary-500', 'text-white');
                e.target.classList.remove('bg-gray-100', 'text-gray-600');
            }
            if (klineDataCache) initKlineChart(klineDataCache);
        }
    });

    // BOLL切换
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('boll-toggle')) {
            activeBOLL = !activeBOLL;
            if (activeBOLL) {
                e.target.classList.add('bg-primary-500', 'text-white');
                e.target.classList.remove('bg-gray-100', 'text-gray-600');
            } else {
                e.target.classList.remove('bg-primary-500', 'text-white');
                e.target.classList.add('bg-gray-100', 'text-gray-600');
            }
            if (klineDataCache) initKlineChart(klineDataCache);
        }
    });

    // 副图指标切换
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('sub-indicator')) {
            document.querySelectorAll('.sub-indicator').forEach(btn => {
                btn.classList.remove('bg-primary-500', 'text-white');
                btn.classList.add('bg-gray-100', 'text-gray-600');
            });
            e.target.classList.add('bg-primary-500', 'text-white');
            e.target.classList.remove('bg-gray-100', 'text-gray-600');
            activeSubIndicator = e.target.dataset.indicator;
            if (klineDataCache) initKlineChart(klineDataCache);
        }
    });
});
