/**
 * K线图模块
 * 
 * 职责:
 * - 从 API 获取股票K线数据（日K/周K/月K）
 * - 初始化 ECharts K线图（含成交量、技术指标）
 * - 支持切换K线周期和技术指标
 * - 主图指标：MA均线（5/10/20/60）、BOLL布林带
 * - 副图指标：成交量、MACD、KDJ、RSI（支持单/双副图模式）
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
let activeSubIndicator = 'volume';   // 副图1：成交量
let dualSubMode = false;              // 双副图模式开关
let activeSubIndicator2 = 'macd';    // 副图2：MACD（默认）

// 筹码峰状态
let activeChips = false;             // 筹码峰开关
let chipsDataCache = null;           // 筹码数据 {available, trade_date, distribution, perf}
let chipsLoading = false;
let chipsConcMode = 90;              // 筹码集中度模式：90 或 70
let _chipsYIdx = -1;                 // 筹码 y 轴索引（datazoom 同步用）
let _chipsDzBound = false;           // datazoom 监听是否已绑定

/** 计算 dataZoom 窗口内 K 线价格范围（含 5% padding） */
function getVisiblePriceRange(data, startPct, endPct) {
    const n = data.length;
    const s = Math.max(0, Math.floor(n * startPct / 100));
    const e = Math.min(n, Math.ceil(n * endPct / 100));
    const win = data.slice(s, e);
    if (!win.length) return { min: 0, max: 1 };
    let lo = Infinity, hi = -Infinity;
    win.forEach(d => { lo = Math.min(lo, +d.low); hi = Math.max(hi, +d.high); });
    const pad = (hi - lo) * 0.05 || 1;
    return { min: +(lo - pad).toFixed(2), max: +(hi + pad).toFixed(2) };
}

/** datazoom 事件同步主图 + 筹码 y 轴范围 */
function syncChipsYAxis() {
    if (!activeChips || _chipsYIdx < 0 || !window.klineChart || !klineDataCache) return;
    const opt = window.klineChart.getOption();
    const dz = opt.dataZoom[0];
    const range = getVisiblePriceRange(klineDataCache.data, dz.start, dz.end);
    const yUp = [];
    yUp[0] = { min: range.min, max: range.max };
    yUp[_chipsYIdx] = { min: range.min, max: range.max };
    window.klineChart.setOption({ yAxis: yUp });
}

function bindChipsDataZoom() {
    if (_chipsDzBound || !window.klineChart) return;
    window.klineChart.on('datazoom', syncChipsYAxis);
    _chipsDzBound = true;
}

// ============================================================
// 技术指标计算模块
// ============================================================

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
            result.push(+(sum / period).toFixed(2));
        }
    }
    return result;
}

/**
 * 计算布林带
 */
function calculateBOLL(data, period = 20, multiplier = 2) {
    const mid = [], upper = [], lower = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            mid.push(null); upper.push(null); lower.push(null);
        } else {
            let sum = 0;
            for (let j = 0; j < period; j++) sum += data[i - j].close;
            const ma = sum / period;
            let variance = 0;
            for (let j = 0; j < period; j++) variance += Math.pow(data[i - j].close - ma, 2);
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
    const dif = [], dea = [], macd = [];
    let shortEMA = 0, longEMA = 0, prevDEA = 0;
    for (let i = 0; i < data.length; i++) {
        const close = +data[i].close;
        if (i === 0) {
            shortEMA = close; longEMA = close;
            dif.push(0); dea.push(0); macd.push(0);
        } else {
            shortEMA = (close * 2 / (shortPeriod + 1)) + (shortEMA * (shortPeriod - 1) / (shortPeriod + 1));
            longEMA = (close * 2 / (longPeriod + 1)) + (longEMA * (longPeriod - 1) / (longPeriod + 1));
            const currentDIF = shortEMA - longEMA;
            const currentDEA = (currentDIF * 2 / (signalPeriod + 1)) + (prevDEA * (signalPeriod - 1) / (signalPeriod + 1));
            const currentMACD = (currentDIF - currentDEA) * 2;
            dif.push(+currentDIF.toFixed(3));
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
    const kArr = [], dArr = [], jArr = [];
    let prevK = 50, prevD = 50;
    for (let i = 0; i < data.length; i++) {
        if (i < n - 1) {
            kArr.push(null); dArr.push(null); jArr.push(null);
        } else {
            let highest = -Infinity, lowest = Infinity;
            for (let idx = 0; idx < n; idx++) {
                highest = Math.max(highest, +data[i - idx].high);
                lowest = Math.min(lowest, +data[i - idx].low);
            }
            const close = +data[i].close;
            const rsv = highest === lowest ? 50 : ((close - lowest) / (highest - lowest)) * 100;
            const currentK = (rsv * 2 / m1) + (prevK * (m1 - 1) / m1);
            const currentD = (currentK * 2 / m2) + (prevD * (m2 - 1) / m2);
            const currentJ = 3 * currentK - 2 * currentD;
            kArr.push(+currentK.toFixed(2));
            dArr.push(+currentD.toFixed(2));
            jArr.push(+currentJ.toFixed(2));
            prevK = currentK; prevD = currentD;
        }
    }
    return { k: kArr, d: dArr, j: jArr };
}

/**
 * 计算RSI
 */
function calculateRSI(data, period = 14) {
    const rsi = [];
    let avgGain = 0, avgLoss = 0;
    for (let i = 0; i < data.length; i++) {
        if (i === 0) { rsi.push(null); continue; }
        const change = +data[i].close - +data[i - 1].close;
        const gain = change > 0 ? change : 0;
        const loss = change < 0 ? -change : 0;
        if (i <= period) {
            avgGain += gain; avgLoss += loss;
            if (i === period) {
                avgGain /= period; avgLoss /= period;
                const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
                rsi.push(+(100 - 100 / (1 + rs)).toFixed(2));
            } else { rsi.push(null); }
        } else {
            avgGain = (avgGain * (period - 1) + gain) / period;
            avgLoss = (avgLoss * (period - 1) + loss) / period;
            const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
            rsi.push(+(100 - 100 / (1 + rs)).toFixed(2));
        }
    }
    return rsi;
}

// ============================================================
// 副图渲染模块
// ============================================================

/**
 * 构建单个副图的 grid / xAxis / yAxis / series 配置
 * 
 * @param {string} indicator - 指标类型：'volume' | 'macd' | 'kdj' | 'rsi'
 * @param {Array} dates - 日期数组
 * @param {Array} volumes - 成交量数据
 * @param {Array} data - 原始K线数据
 * @param {number} gridIndex - 当前副图在 grid 中的索引
 * @param {string} top - 副图区域顶部位置（如 '72%'）
 * @param {string} height - 副图区域高度（如 '18%'）
 * @returns {Object} 包含 grid, xAxis, yAxis, series, legendItems 的配置对象
 */
function buildSubIndicatorConfig(indicator, dates, volumes, data, gridIndex, top, height) {
    const config = {
        grid: { left: 60, right: 20, top: top, height: height },
        xAxis: {
            type: 'category',
            data: dates,
            gridIndex: gridIndex,
            axisLabel: { show: false },
            axisTick: { show: false }
        },
        yAxis: null,
        series: [],
        legendItems: []
    };

    switch (indicator) {
        case 'volume':
            config.yAxis = {
                scale: true,
                gridIndex: gridIndex,
                splitLine: { show: false },
                axisLabel: {
                    fontSize: 10, color: '#888',
                    formatter: function(value) { return (value / 10000).toFixed(0) + '万'; }
                }
            };
            config.series.push({
                name: '成交量',
                type: 'bar',
                xAxisIndex: gridIndex,
                yAxisIndex: gridIndex,
                data: volumes.map(v => ({
                    value: v[1],
                    itemStyle: { color: v[2] >= 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(34, 197, 94, 0.6)' }
                }))
            });
            break;

        case 'macd': {
            const macd = calculateMACD(data);
            config.yAxis = {
                scale: true,
                gridIndex: gridIndex,
                splitLine: { lineStyle: { color: '#f0f0f0' } },
                axisLabel: {
                    fontSize: 10, color: '#888',
                    formatter: function(value) { return value.toFixed(2); }
                }
            };
            // 零轴参考线
            config.series.push({
                name: '_macd_zero_' + gridIndex,
                type: 'line',
                data: dates.map(() => 0),
                lineStyle: { width: 1, color: '#999', type: 'solid' },
                symbol: 'none',
                xAxisIndex: gridIndex, yAxisIndex: gridIndex,
                silent: true
            });
            config.legendItems = ['DIF', 'DEA', 'MACD'];
            config.series.push(
                {
                    name: 'DIF', type: 'line', data: macd.dif, smooth: true,
                    lineStyle: { width: 1, color: '#3b82f6' },
                    symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex
                },
                {
                    name: 'DEA', type: 'line', data: macd.dea, smooth: true,
                    lineStyle: { width: 1, color: '#f59e0b' },
                    symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex
                },
                {
                    name: 'MACD', type: 'bar',
                    xAxisIndex: gridIndex, yAxisIndex: gridIndex,
                    data: macd.macd.map(v => ({
                        value: v,
                        itemStyle: { color: v >= 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(34, 197, 94, 0.6)' }
                    }))
                }
            );
            break;
        }

        case 'kdj': {
            const kdj = calculateKDJ(data);
            config.yAxis = {
                scale: true,
                gridIndex: gridIndex,
                splitLine: { lineStyle: { color: '#f0f0f0' } },
                axisLabel: { fontSize: 10, color: '#888' }
            };
            // 参考线 20/80
            config.series.push(
                {
                    name: '_kdj_20_' + gridIndex, type: 'line',
                    data: dates.map(() => 20),
                    lineStyle: { width: 1, color: '#ccc', type: 'dashed' },
                    symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex, silent: true
                },
                {
                    name: '_kdj_80_' + gridIndex, type: 'line',
                    data: dates.map(() => 80),
                    lineStyle: { width: 1, color: '#ccc', type: 'dashed' },
                    symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex, silent: true
                }
            );
            config.legendItems = ['K', 'D', 'J'];
            config.series.push(
                {
                    name: 'K', type: 'line', data: kdj.k, smooth: true,
                    lineStyle: { width: 1, color: '#3b82f6' },
                    symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex
                },
                {
                    name: 'D', type: 'line', data: kdj.d, smooth: true,
                    lineStyle: { width: 1, color: '#f59e0b' },
                    symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex
                },
                {
                    name: 'J', type: 'line', data: kdj.j, smooth: true,
                    lineStyle: { width: 1, color: '#8b5cf6' },
                    symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex
                }
            );
            break;
        }

        case 'rsi': {
            const rsiData = calculateRSI(data);
            config.yAxis = {
                min: 0, max: 100, interval: 20,
                gridIndex: gridIndex,
                splitLine: { lineStyle: { color: '#f0f0f0' } },
                axisLabel: { fontSize: 10, color: '#888' }
            };
            // 参考线 30/70
            config.series.push(
                {
                    name: '_rsi_30_' + gridIndex, type: 'line',
                    data: dates.map(() => 30),
                    lineStyle: { width: 1, color: '#22c55e', type: 'dashed' },
                    symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex, silent: true
                },
                {
                    name: '_rsi_70_' + gridIndex, type: 'line',
                    data: dates.map(() => 70),
                    lineStyle: { width: 1, color: '#ef4444', type: 'dashed' },
                    symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex, silent: true
                }
            );
            config.legendItems = ['RSI'];
            config.series.push({
                name: 'RSI', type: 'line', data: rsiData, smooth: true,
                lineStyle: { width: 1, color: '#8b5cf6' },
                symbol: 'none', xAxisIndex: gridIndex, yAxisIndex: gridIndex
            });
            break;
        }
    }

    return config;
}

// ============================================================
// 图表容器高度管理
// ============================================================

/**
 * 根据当前模式调整图表容器高度
 */
function updateChartContainerHeight() {
    const areaDom = document.getElementById('kline-chart-area');
    if (!areaDom) return;
    
    if (dualSubMode) {
        areaDom.className = 'relative w-full h-[26rem] sm:h-[32rem] lg:h-[38rem]';
    } else {
        areaDom.className = 'relative w-full h-80 sm:h-96 lg:h-[28rem]';
    }
}

// ============================================================
// 数据加载与图表初始化
// ============================================================

/**
 * 加载K线数据并渲染图表
 */
async function loadKline(period = 'daily') {
    try {
        const count = period === 'daily' ? 120 : 150;
        const res = await fetch(`/api/stock/${STOCK_CODE}/kline?period=${period}&count=${count}`);
        const data = await res.json();

        if (data && data.data && data.data.length > 0) {
            const lastTradeDate = data.data[data.data.length - 1].trade_date;
            const dateHint = document.getElementById('data-hint');
            if (lastTradeDate && dateHint) {
                const year = lastTradeDate.slice(0, 4);
                const month = parseInt(lastTradeDate.slice(4, 6));
                const day = parseInt(lastTradeDate.slice(6, 8));
                dateHint.textContent = `数据截止${year}-${month}-${day}，交易日数据在收盘后60分钟刷新！`;
            }

            klineDataCache = data;

            document.getElementById('kline-skeleton').classList.add('hidden');
            document.getElementById('kline-content').classList.remove('hidden');

            // 更新容器高度后再初始化图表
            updateChartContainerHeight();

            requestAnimationFrame(() => {
                initKlineChart(data);
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

    const dates = klineData.data.map(item => item.trade_date);
    const values = klineData.data.map(item => [item.open, item.close, item.low, item.high]);
    const volumes = klineData.data.map((item, index) => {
        const isUp = item.close >= item.open;
        return [index, item.vol || 0, isUp ? 1 : -1];
    });

    // 计算MA
    const maData = {};
    activeMA.forEach(period => { maData[period] = calculateMA(klineData.data, period); });

    // ========== 决定布局 ==========
    const isDual = dualSubMode && activeSubIndicator2 !== activeSubIndicator;

    // 主图高度
    const mainTop = 40;
    const mainHeight = isDual ? '38%' : '55%';
    // 副图布局参数
    const subHeight = '18%';
    const sub1Top = isDual ? '50%' : '72%';
    const sub2Top = '74%';

    // 筹码布局预计算
    const chipsActive = activeChips && chipsDataCache && chipsDataCache.available
        && chipsDataCache.distribution && chipsDataCache.distribution.length > 0;
    const chipsRight = chipsActive ? '35%' : 20;
    let chipsPriceRange = null;
    if (chipsActive) {
        chipsPriceRange = getVisiblePriceRange(klineData.data, 50, 100);
    }
    _chipsYIdx = -1; // 重置，后面赋值

    // ========== 构建基础配置 ==========
    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross', lineStyle: { color: '#888', type: 'dashed' } },
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#ddd',
            borderWidth: 1,
            textStyle: { color: '#333', fontSize: 12 }
        },
        legend: { data: [], top: 5, textStyle: { fontSize: 10 } },
        grid: [
            { left: 60, right: chipsRight, top: mainTop, height: mainHeight }
        ],
        xAxis: [{
            type: 'category',
            data: dates,
            gridIndex: 0,
            axisLabel: {
                fontSize: 10, color: '#888', rotate: 30,
                formatter: function(value) { return value.slice(4, 6) + '-' + value.slice(6, 8); }
            },
            axisTick: { show: false }
        }],
        yAxis: [{
            scale: true,
            gridIndex: 0,
            splitLine: { lineStyle: { color: '#f0f0f0' } },
            axisLabel: { fontSize: 10, color: '#888' },
            ...(chipsActive ? { min: chipsPriceRange.min, max: chipsPriceRange.max } : {})
        }],
        dataZoom: [{
            type: 'inside',
            xAxisIndex: [0],  // 占位，后面动态填充
            start: 50, end: 100
        }, {
            type: 'slider',
            xAxisIndex: [0],  // 占位，后面动态填充
            bottom: 5, height: 14,
            borderColor: 'transparent',
            backgroundColor: '#f5f5f5',
            fillerColor: 'rgba(59, 130, 246, 0.2)',
            handleStyle: { color: '#3b82f6' },
            textStyle: { color: '#888', fontSize: 10 }
        }],
        series: [{
            name: 'K线',
            type: 'candlestick',
            data: values,
            itemStyle: {
                color: '#ef4444', color0: '#22c55e',
                borderColor: '#ef4444', borderColor0: '#22c55e'
            }
        }]
    };

    // ========== 主图叠加指标 ==========
    const maColors = { 5: '#f59e0b', 10: '#3b82f6', 20: '#8b5cf6', 60: '#ef4444' };
    activeMA.forEach(period => {
        option.legend.data.push(`MA${period}`);
        option.series.push({
            name: `MA${period}`, type: 'line', data: maData[period],
            smooth: true, lineStyle: { width: 1, color: maColors[period] },
            symbol: 'none', xAxisIndex: 0, yAxisIndex: 0
        });
    });

    if (activeBOLL) {
        const boll = calculateBOLL(klineData.data);
        option.legend.data.push('BOLL中轨', 'BOLL上轨', 'BOLL下轨');
        option.series.push(
            {
                name: 'BOLL中轨', type: 'line', data: boll.mid, smooth: true,
                lineStyle: { width: 1, color: '#f59e0b' },
                symbol: 'none', xAxisIndex: 0, yAxisIndex: 0
            },
            {
                name: 'BOLL上轨', type: 'line', data: boll.upper, smooth: true,
                lineStyle: { width: 1, color: '#ef4444', type: 'dashed' },
                symbol: 'none', xAxisIndex: 0, yAxisIndex: 0
            },
            {
                name: 'BOLL下轨', type: 'line', data: boll.lower, smooth: true,
                lineStyle: { width: 1, color: '#22c55e', type: 'dashed' },
                symbol: 'none', xAxisIndex: 0, yAxisIndex: 0
            }
        );
    }

    // ========== 筹码峰（独立右侧网格，参考东方财富布局） ==========
    if (chipsActive) {
        const chips = chipsDataCache.distribution;
        const currentPrice = klineData.data[klineData.data.length - 1].close;
        // 健壮最大值：忽略非有限值，避免极端数据下 max 退化
        // 且不做余量缩放——最长柱顶满筹码区右边缘，
        // 否则平台型筹码（密集区多行≈max）会在右侧吊一条空白，看起来像被截断
        const maxPercent = (function(){
            let m = 0;
            for (let i = 0; i < chips.length; i++) {
                const p = chips[i].percent;
                if (typeof p === 'number' && isFinite(p) && p > m) m = p;
            }
            return m || 1;
        })();
        const priceStep = chips.length > 1 ? Math.abs(chips[1].price - chips[0].price) : 1;

        // 筹码网格（右侧独立区域）
        // show+淡底色：让整块筹码矩形有"画布感"，
        // 比例缩放产生的右侧留白看起来是背景而非"被截断"
        const cGridIdx = option.grid.length;
        option.grid.push({
            left: '65%', right: 6, top: mainTop, height: mainHeight,
            show: true, backgroundColor: 'rgba(15, 23, 42, 0.025)',
            borderColor: 'rgba(15, 23, 42, 0.06)', borderWidth: 1
        });

        // 筹码 x 轴（百分比，横向柱长度）
        const cXIdx = option.xAxis.length;
        option.xAxis.push({ type: 'value', gridIndex: cGridIdx, show: false, max: maxPercent });

        // 筹码 y 轴（价格，与主图同步）
        const cYIdx = option.yAxis.length;
        _chipsYIdx = cYIdx;
        option.yAxis.push({ type: 'value', gridIndex: cGridIdx, show: false, min: chipsPriceRange.min, max: chipsPriceRange.max });

         // 横向柱状图（custom series）
        option.series.push({
            name: '筹码分布', type: 'custom',
            xAxisIndex: cXIdx, yAxisIndex: cYIdx,
            silent: true, encode: { x: 0, y: 1 },
            renderItem: function(params, api) {
                const cs = params.coordSys;
                if (!cs) return { type: 'group', children: [] };
                const price = api.value(1);
                const percent = api.value(0);
                const origin = api.coord([0, price]);
                const end = api.coord([percent || 0, price]);
                const nextY = api.coord([0, price + priceStep]);
                const barH = Math.max(1, Math.abs(origin[1] - nextY[1]) + 0.5);
                const barW = Math.max(1, end[0] - origin[0]);
                return {
                    type: 'rect',
                    shape: { x: origin[0], y: origin[1] - barH / 2, width: barW, height: barH },
                    style: { fill: price < currentPrice ? '#ef4444' : '#22c55e', opacity: 0.85 },
                    silent: true
                };
            },
            data: chips.map(c => [c.percent, c.price])
        });
    }

    // ========== 副图1 ==========
    const sub1Idx = option.grid.length; // 动态索引，兼容筹码峰偏移
    const sub1 = buildSubIndicatorConfig(
        activeSubIndicator, dates, volumes, klineData.data,
        sub1Idx, sub1Top, subHeight
    );
    if (chipsActive) sub1.grid.right = chipsRight;
    option.grid.push(sub1.grid);
    option.xAxis.push(sub1.xAxis);
    option.yAxis.push(sub1.yAxis);
    option.series.push(...sub1.series);
    option.legend.data.push(...sub1.legendItems);

    // ========== 副图2（双副图模式） ==========
    if (isDual) {
        const sub2Idx = option.grid.length; // 动态索引
        const sub2 = buildSubIndicatorConfig(
            activeSubIndicator2, dates, volumes, klineData.data,
            sub2Idx, sub2Top, subHeight
        );
        if (chipsActive) sub2.grid.right = chipsRight;
        option.grid.push(sub2.grid);
        option.xAxis.push(sub2.xAxis);
        option.yAxis.push(sub2.yAxis);
        option.series.push(...sub2.series);
        option.legend.data.push(...sub2.legendItems);
    }

    // ========== 动态修正 dataZoom xAxisIndex ==========
    // 只关联 category 类型的 xAxis（跳过筹码峰的 value 轴）
    const categoryXIndices = [];
    option.xAxis.forEach((ax, i) => { if (ax.type === 'category') categoryXIndices.push(i); });
    option.dataZoom.forEach(dz => { dz.xAxisIndex = categoryXIndices; });

    window.klineChart.setOption(option, { notMerge: true });

    // 绑定 datazoom 同步（筹码 y 轴跟随主图缩放）
    if (chipsActive) bindChipsDataZoom();
}

// ============================================================
// 筹码峰数据加载与信息栏
// ============================================================

/**
 * 加载筹码分布数据
 */
async function loadChips() {
    if (chipsLoading) return;
    chipsLoading = true;
    try {
        const res = await fetch(`/api/stock/${STOCK_CODE}/chips`);
        chipsDataCache = await res.json();
    } catch (err) {
        console.error('[kline-chart] 加载筹码数据失败:', err);
        chipsDataCache = { available: false };
    } finally {
        chipsLoading = false;
    }
    if (klineDataCache) initKlineChart(klineDataCache);
    updateChipsInfo();
}

/**
 * 更新筹码统计面板（右侧独立区域，参考东方财富布局）
 */
function updateChipsInfo() {
    const panel = document.getElementById('chips-stats-panel');
    if (!panel) return;

    if (!activeChips) {
        panel.classList.add('hidden');
        panel.innerHTML = '';
        return;
    }

    // 动态调整面板位置：紧贴筹码峰底部下方，避免遮挡筹码峰
    const isDual = dualSubMode && activeSubIndicator2 !== activeSubIndicator;
    const areaEl = document.getElementById('kline-chart-area');
    const H = areaEl ? areaEl.clientHeight : 400;
    const mainH = isDual ? 0.38 : 0.55;            // 与 initKlineChart 的 mainHeight 保持一致
    const chipsBottomPx = 40 + mainH * H;          // mainTop(40) + 主图/筹码高度
    panel.style.top = (chipsBottomPx + 12) + 'px';
    panel.style.bottom = '26px';                    // 给 dataZoom slider 留出空间
    panel.classList.remove('hidden');

    if (chipsLoading || chipsDataCache === null) {
        panel.innerHTML = '<div class="text-gray-400 text-center mt-4">加载中…</div>';
        return;
    }
    if (!chipsDataCache.available) {
        panel.innerHTML = '<div class="text-gray-400 text-center mt-4">暂无筹码数据<br><span class="text-[10px]">自 2018 年起提供</span></div>';
        return;
    }

    const p = chipsDataCache.perf || {};
    const d = chipsDataCache.trade_date || '';
    const dateStr = d && d.length === 8 ? `${d.slice(0,4)}-${d.slice(4,6)}-${d.slice(6,8)}` : '--';
    const v = (x, s='') => x != null ? x + s : '--';

    // 集中度计算
    const is90 = chipsConcMode === 90;
    const cLo = is90 ? p.cost_5pct : p.cost_15pct;
    const cHi = is90 ? p.cost_95pct : p.cost_85pct;
    const cMid = p.cost_50pct;
    const conc = (cLo != null && cHi != null && cMid) ? ((cHi - cLo) / cMid * 100).toFixed(2) : null;

    const btn90 = is90 ? 'bg-gray-700 text-white' : 'bg-gray-200 text-gray-600 hover:bg-gray-300';
    const btn70 = !is90 ? 'bg-gray-700 text-white' : 'bg-gray-200 text-gray-600 hover:bg-gray-300';

    panel.innerHTML = `
        <div class="space-y-2">
            <!-- 图例 -->
            <div class="flex items-center gap-3 text-[11px]">
                <span class="flex items-center gap-1"><i class="w-2.5 h-2.5 rounded-sm inline-block" style="background:#22c55e"></i>套牢</span>
                <span class="flex items-center gap-1"><i class="w-2.5 h-2.5 rounded-sm inline-block" style="background:#ef4444"></i>获利</span>
            </div>
            <!-- 核心指标 -->
            <div class="space-y-1.5">
                <div class="flex justify-between"><span class="text-gray-500">获利比例</span><b class="text-red-500 tabular-nums">${v(p.winner_rate,'%')}</b></div>
                <div class="flex justify-between"><span class="text-gray-500">平均成本</span><b class="text-purple-600 tabular-nums">${v(p.weight_avg)}</b></div>
            </div>
            <!-- 集中度切换 -->
            <div class="flex gap-1">
                <button class="chips-conc-btn btn-press flex-1 py-1 text-[11px] rounded ${btn90}" data-mode="90">90%筹码</button>
                <button class="chips-conc-btn btn-press flex-1 py-1 text-[11px] rounded ${btn70}" data-mode="70">70%筹码</button>
            </div>
            <div class="space-y-1.5">
                <div class="flex justify-between"><span class="text-gray-500">价格区间</span><b class="tabular-nums">${v(cLo)}–${v(cHi)}</b></div>
                <div class="flex justify-between"><span class="text-gray-500">集中度</span><b class="tabular-nums">${conc != null ? conc+'%' : '--'}</b></div>
            </div>
            <!-- 日期提示 -->
            <div class="pt-1 border-t border-gray-200">
                <div class="flex justify-between text-[10px] text-gray-400">
                    <span title="筹码数据每日 18:00-19:00 更新">说明 ⓘ</span>
                    <span class="tabular-nums">${dateStr}</span>
                </div>
            </div>
        </div>
    `;
}

// ============================================================
// 事件监听
// ============================================================

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
            e.target.classList.toggle('bg-primary-500');
            e.target.classList.toggle('text-white');
            e.target.classList.toggle('bg-gray-100');
            e.target.classList.toggle('text-gray-600');
            if (klineDataCache) initKlineChart(klineDataCache);
        }
    });

    // 副图1切换
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('sub-indicator')) {
            document.querySelectorAll('.sub-indicator').forEach(btn => {
                btn.classList.remove('bg-primary-500', 'text-white');
                btn.classList.add('bg-gray-100', 'text-gray-600');
            });
            e.target.classList.add('bg-primary-500', 'text-white');
            e.target.classList.remove('bg-gray-100', 'text-gray-600');
            activeSubIndicator = e.target.dataset.indicator;
            
            // 双副图模式下，副图2不能与副图1相同，自动切换
            if (dualSubMode && activeSubIndicator2 === activeSubIndicator) {
                const alternatives = ['volume', 'macd', 'kdj', 'rsi'].filter(i => i !== activeSubIndicator);
                activeSubIndicator2 = alternatives[0];
                updateSubIndicator2Buttons();
            }
            
            if (klineDataCache) initKlineChart(klineDataCache);
        }
    });

    // 副图2切换
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('sub-indicator-2')) {
            document.querySelectorAll('.sub-indicator-2').forEach(btn => {
                btn.classList.remove('bg-primary-500', 'text-white');
                btn.classList.add('bg-gray-100', 'text-gray-600');
            });
            e.target.classList.add('bg-primary-500', 'text-white');
            e.target.classList.remove('bg-gray-100', 'text-gray-600');
            activeSubIndicator2 = e.target.dataset.indicator;
            if (klineDataCache) initKlineChart(klineDataCache);
        }
    });

    // 筹码峰开关
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.chips-toggle');
        if (!btn) return;

        activeChips = !activeChips;
        btn.classList.toggle('bg-primary-500', activeChips);
        btn.classList.toggle('text-white', activeChips);
        btn.classList.toggle('bg-gray-100', !activeChips);
        btn.classList.toggle('text-gray-600', !activeChips);

        if (activeChips && chipsDataCache === null) {
            updateChipsInfo();
            loadChips();
        } else {
            if (klineDataCache) initKlineChart(klineDataCache);
            updateChipsInfo();
        }
    });

    // 筹码集中度切换（90% / 70%）
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.chips-conc-btn');
        if (!btn) return;
        chipsConcMode = parseInt(btn.dataset.mode) || 90;
        updateChipsInfo();
    });

    // 双副图开关
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('#dual-sub-toggle');
        if (!btn) return;
        
        dualSubMode = !dualSubMode;
        const wrapper = document.getElementById('sub-indicator-2-wrapper');
        
        if (dualSubMode) {
            btn.classList.add('bg-primary-500', 'text-white');
            btn.classList.remove('bg-gray-100', 'text-gray-600');
            wrapper.classList.remove('hidden');
            
            // 确保副图2与副图1不同
            if (activeSubIndicator2 === activeSubIndicator) {
                const alternatives = ['volume', 'macd', 'kdj', 'rsi'].filter(i => i !== activeSubIndicator);
                activeSubIndicator2 = alternatives[0];
                updateSubIndicator2Buttons();
            }
        } else {
            btn.classList.remove('bg-primary-500', 'text-white');
            btn.classList.add('bg-gray-100', 'text-gray-600');
            wrapper.classList.add('hidden');
        }
        
        // 更新容器高度并重绘
        if (klineDataCache) {
            updateChartContainerHeight();
            // 延迟一帧让DOM完成高度变化
            requestAnimationFrame(() => {
                if (window.klineChart) window.klineChart.resize();
                initKlineChart(klineDataCache);
            });
        }
    });
});

// ============================================================
// 画布尺寸自适应（ResizeObserver + window resize）
// ============================================================
// ECharts init 时把 canvas style.width/height 设为固定像素。
// 若容器后来变宽（暗色主题扩展注入 CSS、web 字体 reflow、
// 侧边栏折叠等），canvas 不会自动跟着变，右侧空一条。
// ResizeObserver 能捕获任何容器尺寸变化并触发 resize()。
(function setupChartResize() {
    function doResize() {
        if (window.klineChart) window.klineChart.resize();
    }
    // 优先 ResizeObserver（捕获非 window-resize 的容器变化）
    if (typeof ResizeObserver !== 'undefined') {
        const ro = new ResizeObserver(function(entries) {
            // 防抖：一帧内只 resize 一次
            requestAnimationFrame(doResize);
        });
        // 等 DOM 就绪后观察容器
        document.addEventListener('DOMContentLoaded', function() {
            const el = document.getElementById('kline-chart');
            if (el) ro.observe(el);
        });
    }
    // 兜底：window resize
    window.addEventListener('resize', doResize);
})();

/**
 * 更新副图2按钮的选中状态
 */
function updateSubIndicator2Buttons() {
    document.querySelectorAll('.sub-indicator-2').forEach(btn => {
        if (btn.dataset.indicator === activeSubIndicator2) {
            btn.classList.add('bg-primary-500', 'text-white');
            btn.classList.remove('bg-gray-100', 'text-gray-600');
        } else {
            btn.classList.remove('bg-primary-500', 'text-white');
            btn.classList.add('bg-gray-100', 'text-gray-600');
        }
    });
}
