"""技术面分析引擎

实现常用技术指标计算、形态识别、支撑阻力位、买卖信号生成
"""
from typing import List, Dict, Optional, Any
import numpy as np


class TechnicalAnalyzer:
    """技术面分析器"""

    def __init__(self):
        self.kline_data: List[Dict] = []
        self.closes: np.ndarray = np.array([])
        self.highs: np.ndarray = np.array([])
        self.lows: np.ndarray = np.array([])
        self.opens: np.ndarray = np.array([])
        self.volumes: np.ndarray = np.array([])

    def analyze(self, code: str, count: int = 120, preloaded: Dict[str, Any] = None) -> Dict:
        """
        对指定股票进行完整技术面分析

        Args:
            code: 股票代码
            count: 获取K线数量（默认120根日K）
            preloaded: 预加载数据字典（来自 DataCollector），含 kline

        Returns:
            包含所有技术指标、形态、信号的分析结果
        """
        # 使用预加载数据或自行获取
        if preloaded and preloaded.get('kline'):
            kline = preloaded['kline']
            if len(kline) < 30:
                return {"error": f"数据不足，无法进行技术分析（需要至少30根K线）", "code": code}
        else:
            from app.services.data.stock_service import stock_service
            # 获取K线数据
            kline = stock_service.get_kline(code, period='daily', count=count)
            if not kline or len(kline) < 30:
                return {"error": f"数据不足，无法进行技术分析（需要至少30根K线）", "code": code}

        self.kline_data = kline
        self._prepare_arrays()

        # 计算各技术指标并缓存到实例变量（避免重复计算）
        self._ma_result = self._calc_ma()
        self._macd_result = self._calc_macd()
        self._kdj_result = self._calc_kdj()
        self._rsi_result = self._calc_rsi()
        self._boll_result = self._calc_boll()
        self._volume_result = self._calc_volume()
        self._patterns_result = self._detect_patterns()
        self._support_resistance_result = self._calc_support_resistance()

        result = {
            "code": code,
            "analysis_time": self._now(),
            "kline_count": len(kline),
            "ma": self._ma_result,
            "macd": self._macd_result,
            "kdj": self._kdj_result,
            "rsi": self._rsi_result,
            "boll": self._boll_result,
            "volume": self._volume_result,
            "patterns": self._patterns_result,
            "support_resistance": self._support_resistance_result,
            "signals": self._generate_signals(),
            "score": self._calc_technical_score()
        }

        return result

    def _prepare_arrays(self):
        """将K线数据转换为numpy数组方便计算"""
        self.closes = np.array([k["close"] for k in self.kline_data], dtype=float)
        self.highs = np.array([k["high"] for k in self.kline_data], dtype=float)
        self.lows = np.array([k["low"] for k in self.kline_data], dtype=float)
        self.opens = np.array([k["open"] for k in self.kline_data], dtype=float)
        self.volumes = np.array([k["vol"] for k in self.kline_data], dtype=float)

    # ==================== 均线系统 ====================

    def _calc_ma(self) -> Dict:
        """计算移动平均线系统"""
        periods = [5, 10, 20, 60, 120, 250]
        ma_values = {}

        for p in periods:
            if len(self.closes) >= p:
                ma = self._sma(self.closes, p)
                ma_values[f"ma{p}"] = round(ma[-1], 3) if len(ma) > 0 else None
            else:
                ma_values[f"ma{p}"] = None

        # 判断多空排列
        ma_list = []
        for p in [5, 10, 20, 60]:
            val = ma_values.get(f"ma{p}")
            if val is not None:
                ma_list.append((p, val))

        arrangement = "unknown"
        if len(ma_list) >= 4:
            vals = [v for _, v in ma_list]
            if vals[0] > vals[1] > vals[2] > vals[3]:
                arrangement = "bullish"  # 多头排列
            elif vals[0] < vals[1] < vals[2] < vals[3]:
                arrangement = "bearish"  # 空头排列
            else:
                arrangement = "mixed"  # 交叉排列

        # 判断当前价格与均线的关系
        current_price = self.closes[-1]
        above_count = sum(1 for _, v in ma_list if current_price > v)
        price_position = f"above_{above_count}_ma" if above_count > len(ma_list) / 2 else f"below_{len(ma_list) - above_count}_ma"

        # 均线金叉/死叉检测（短期穿越长期）
        crosses = self._detect_ma_cross()

        return {
            "values": ma_values,
            "arrangement": arrangement,
            "price_position": price_position,
            "above_ma_count": above_count,
            "total_ma_count": len(ma_list),
            "crosses": crosses,
        }

    def _detect_ma_cross(self) -> List[Dict]:
        """检测均线交叉"""
        crosses = []
        if len(self.closes) < 20:
            return crosses

        # 检测MA5与MA20的交叉
        ma5 = self._sma(self.closes, 5)
        ma20 = self._sma(self.closes, 20)

        if len(ma5) >= 2 and len(ma20) >= 2:
            # 最近2根K线
            diff_prev = ma5[-2] - ma20[-2]
            diff_curr = ma5[-1] - ma20[-1]

            if diff_prev <= 0 < diff_curr:
                crosses.append({"type": "golden", "periods": (5, 20), "desc": "MA5上穿MA20，短期金叉"})
            elif diff_prev >= 0 > diff_curr:
                crosses.append({"type": "death", "periods": (5, 20), "desc": "MA5下穿MA20，短期死叉"})

        return crosses

    # ==================== MACD ====================

    def _calc_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """计算MACD指标"""
        ema_fast = self._ema(self.closes, fast)
        ema_slow = self._ema(self.closes, slow)

        dif = ema_fast - ema_slow
        dea = self._ema(dif, signal)
        macd_hist = 2 * (dif - dea)

        # 金叉/死叉
        golden_cross = False
        death_cross = False
        if len(dif) >= 2 and len(dea) >= 2:
            diff_prev = dif[-2] - dea[-2]
            diff_curr = dif[-1] - dea[-1]
            if diff_prev <= 0 < diff_curr:
                golden_cross = True
            elif diff_prev >= 0 > diff_curr:
                death_cross = True

        # 顶底背离检测
        divergence = self._detect_macd_divergence(dif)

        return {
            "dif": round(float(dif[-1]), 4) if len(dif) > 0 else 0,
            "dea": round(float(dea[-1]), 4) if len(dea) > 0 else 0,
            "macd": round(float(macd_hist[-1]), 4) if len(macd_hist) > 0 else 0,
            "golden_cross": golden_cross,
            "death_cross": death_cross,
            "histogram_trend": "expanding" if abs(macd_hist[-1]) > abs(macd_hist[-2]) else "shrinking" if len(macd_hist) >= 2 else "unknown",
            "zero_axis_position": "above" if dif[-1] > 0 else "below",
            "divergence": divergence,
        }

    def _detect_macd_divergence(self, dif: np.ndarray) -> Dict:
        """检测MACD背离"""
        result = {"top_divergence": False, "bottom_divergence": False, "desc": ""}

        if len(dif) < 30:
            return result

        # 简化版背离检测：比较最近两个高/低点
        # 顶背离：价格创新高但DIF没有
        # 底背离：价格创新低但DIF没有
        lookback = min(60, len(dif))
        recent_closes = self.closes[-lookback:]
        recent_dif = dif[-lookback:]

        # 找价格的局部高点和对应的DIF值
        price_highs = self._find_local_extremes(recent_closes, "max", window=5)
        if len(price_highs) >= 2:
            last_high = price_highs[-1]
            prev_high = price_highs[-2]
            if recent_closes[last_high] > recent_closes[prev_high] and recent_dif[last_high] < recent_dif[prev_high]:
                result["top_divergence"] = True
                result["desc"] = "顶背离：价格创新高但MACD未创新高，注意回调风险"

        # 找价格的局部低点
        price_lows = self._find_local_extremes(recent_closes, "min", window=5)
        if len(price_lows) >= 2:
            last_low = price_lows[-1]
            prev_low = price_lows[-2]
            if recent_closes[last_low] < recent_closes[prev_low] and recent_dif[last_low] > recent_dif[prev_low]:
                result["bottom_divergence"] = True
                result["desc"] = "底背离：价格创新低但MACD未创新低，可能反弹"

        return result

    def _find_local_extremes(self, data: np.ndarray, mode: str, window: int = 5) -> List[int]:
        """找局部极值点索引"""
        extremes = []
        for i in range(window, len(data) - window):
            if mode == "max":
                if data[i] == max(data[i - window:i + window + 1]):
                    extremes.append(i)
            else:
                if data[i] == min(data[i - window:i + window + 1]):
                    extremes.append(i)
        return extremes

    # ==================== KDJ ====================

    def _calc_kdj(self, n: int = 9, m1: int = 3, m2: int = 3) -> Dict:
        """计算KDJ指标"""
        if len(self.closes) < n:
            return {"error": "数据不足"}

        # 计算RSV
        rsv = np.zeros(len(self.closes))
        for i in range(n - 1, len(self.closes)):
            low_n = min(self.lows[i - n + 1:i + 1])
            high_n = max(self.highs[i - n + 1:i + 1])
            if high_n == low_n:
                rsv[i] = 50.0
            else:
                rsv[i] = (self.closes[i] - low_n) / (high_n - low_n) * 100

        # 递推计算K、D
        k_values = np.zeros(len(self.closes))
        d_values = np.zeros(len(self.closes))
        k_values[n - 1] = 50.0
        d_values[n - 1] = 50.0

        for i in range(n, len(self.closes)):
            k_values[i] = (m1 - 1) / m1 * k_values[i - 1] + 1 / m1 * rsv[i]
            d_values[i] = (m2 - 1) / m2 * d_values[i - 1] + 1 / m2 * k_values[i]

        j_values = 3 * k_values - 2 * d_values

        # 金叉/死叉
        golden_cross = False
        death_cross = False
        if len(k_values) >= 2:
            diff_prev = k_values[-2] - d_values[-2]
            diff_curr = k_values[-1] - d_values[-1]
            if diff_prev <= 0 < diff_curr:
                golden_cross = True
            elif diff_prev >= 0 > diff_curr:
                death_cross = True

        # 超买超卖
        zone = "neutral"
        if k_values[-1] > 80 and d_values[-1] > 80:
            zone = "overbought"
        elif k_values[-1] < 20 and d_values[-1] < 20:
            zone = "oversold"

        return {
            "k": round(float(k_values[-1]), 2),
            "d": round(float(d_values[-1]), 2),
            "j": round(float(j_values[-1]), 2),
            "golden_cross": golden_cross,
            "death_cross": death_cross,
            "zone": zone,
        }

    # ==================== RSI ====================

    def _calc_rsi(self) -> Dict:
        """计算RSI指标"""
        periods = [6, 12, 24]
        rsi_values = {}

        for p in periods:
            rsi = self._rsi(self.closes, p)
            if len(rsi) > 0:
                rsi_values[f"rsi{p}"] = round(float(rsi[-1]), 2)

        # 判断超买超卖
        rsi6 = rsi_values.get("rsi6", 50)
        zone = "neutral"
        if rsi6 > 80:
            zone = "overbought"
        elif rsi6 > 70:
            zone = "strong"
        elif rsi6 < 20:
            zone = "oversold"
        elif rsi6 < 30:
            zone = "weak"

        return {
            "values": rsi_values,
            "zone": zone,
            "rsi6_trend": "up" if rsi6 > 50 else "down",
        }

    def _rsi(self, data: np.ndarray, period: int) -> np.ndarray:
        """计算RSI"""
        if len(data) < period + 1:
            return np.array([])

        deltas = np.diff(data)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.zeros(len(deltas))
        avg_loss = np.zeros(len(deltas))

        # 初始值用SMA
        avg_gain[period - 1] = np.mean(gains[:period])
        avg_loss[period - 1] = np.mean(losses[:period])

        # 后续用EMA平滑
        for i in range(period, len(deltas)):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

        with np.errstate(divide='ignore', invalid='ignore'):
            rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100.0)
        rsi = 100 - 100 / (1 + rs)

        return rsi[period - 1:]

    # ==================== 布林带 ====================

    def _calc_boll(self, period: int = 20, num_std: float = 2.0) -> Dict:
        """计算布林带"""
        if len(self.closes) < period:
            return {"error": "数据不足"}

        mid = self._sma(self.closes, period)
        std = self._rolling_std(self.closes, period)

        upper = mid + num_std * std
        lower = mid - num_std * std

        current_price = self.closes[-1]
        current_mid = mid[-1]
        current_upper = upper[-1]
        current_lower = lower[-1]
        bandwidth = (current_upper - current_lower) / current_mid * 100 if current_mid > 0 else 0

        # %B位置: (当前价格 - 下轨) / (上轨 - 下轨)
        pb = (current_price - current_lower) / (current_upper - current_lower) if current_upper != current_lower else 0.5

        # 判断位置
        if current_price >= current_upper:
            position = "above_upper"
        elif current_price <= current_lower:
            position = "below_lower"
        elif current_price > current_mid:
            position = "upper_half"
        else:
            position = "lower_half"

        # 带宽收窄可能变盘
        bandwidth_trend = "narrowing" if bandwidth < 10 else "wide" if bandwidth > 20 else "normal"

        return {
            "upper": round(float(current_upper), 3),
            "mid": round(float(current_mid), 3),
            "lower": round(float(current_lower), 3),
            "bandwidth": round(bandwidth, 2),
            "pb": round(pb, 3),
            "position": position,
            "bandwidth_trend": bandwidth_trend,
        }

    # ==================== 量价分析 ====================

    def _calc_volume(self) -> Dict:
        """量价分析"""
        if len(self.volumes) < 20:
            return {"error": "数据不足"}

        # 量比 = 今日成交量 / 5日平均成交量
        vol_ma5 = np.mean(self.volumes[-5:])
        vol_ma20 = np.mean(self.volumes[-20:])
        volume_ratio = self.volumes[-1] / vol_ma5 if vol_ma5 > 0 else 1

        # OBV (能量潮)
        obv = self._calc_obv()

        # 放量缩量判断
        vol_status = "normal"
        if volume_ratio > 2.0:
            vol_status = "heavy_volume"  # 明显放量
        elif volume_ratio > 1.5:
            vol_status = "increased"  # 温和放量
        elif volume_ratio < 0.5:
            vol_status = "heavy_shrink"  # 明显缩量
        elif volume_ratio < 0.7:
            vol_status = "shrunk"  # 缩量

        # 量价配合判断
        price_up = self.closes[-1] > self.closes[-2]
        vol_up = self.volumes[-1] > self.volumes[-2]
        coordination = "unknown"
        if price_up and vol_up:
            coordination = "price_vol_up"  # 量价齐升（健康上涨）
        elif price_up and not vol_up:
            coordination = "price_up_vol_down"  # 价升量缩（上涨乏力）
        elif not price_up and vol_up:
            coordination = "price_down_vol_up"  # 价跌量增（可能恐慌）
        elif not price_up and not vol_up:
            coordination = "price_vol_down"  # 量价齐跌（缩量阴跌或洗盘）

        # 换手率趋势（用成交量变化代替）
        vol_trend_5d = (self.volumes[-1] / self.volumes[-5] - 1) * 100 if self.volumes[-5] > 0 else 0

        return {
            "volume_ratio": round(float(volume_ratio), 2),
            "vol_status": vol_status,
            "coordination": coordination,
            "obv": round(float(obv[-1]), 0) if len(obv) > 0 else 0,
            "vol_ma5": round(float(vol_ma5), 0),
            "vol_ma20": round(float(vol_ma20), 0),
            "vol_trend_5d": round(float(vol_trend_5d), 2),
        }

    def _calc_obv(self) -> np.ndarray:
        """计算OBV能量潮"""
        obv = np.zeros(len(self.closes))
        for i in range(1, len(self.closes)):
            if self.closes[i] > self.closes[i - 1]:
                obv[i] = obv[i - 1] + self.volumes[i]
            elif self.closes[i] < self.closes[i - 1]:
                obv[i] = obv[i - 1] - self.volumes[i]
            else:
                obv[i] = obv[i - 1]
        return obv

    # ==================== K线形态识别 ====================

    def _detect_patterns(self) -> List[Dict]:
        """K线形态识别"""
        patterns = []

        if len(self.kline_data) < 5:
            return patterns

        # 最近几根K线
        last = self.kline_data[-1]
        prev = self.kline_data[-2] if len(self.kline_data) >= 2 else None

        # 1. 十字星
        body = abs(last["close"] - last["open"])
        total_range = last["high"] - last["low"]
        if total_range > 0 and body / total_range < 0.1:
            patterns.append({
                "name": "十字星",
                "signal": "neutral",
                "desc": "多空力量平衡，可能变盘",
                "reliability": "medium"
            })

        # 2. 锤子线（下影线长、实体小、上影线短）
        upper_shadow = last["high"] - max(last["open"], last["close"])
        lower_shadow = min(last["open"], last["close"]) - last["low"]
        if lower_shadow > body * 2 and upper_shadow < body * 0.5 and body > 0:
            # 检查是否在下跌趋势中
            if len(self.closes) >= 10 and self.closes[-1] < np.mean(self.closes[-10:]):
                patterns.append({
                    "name": "锤子线",
                    "signal": "bullish",
                    "desc": "下跌趋势中出现锤子线，可能见底反转",
                    "reliability": "medium"
                })

        # 3. 倒锤子线
        if upper_shadow > body * 2 and lower_shadow < body * 0.5 and body > 0:
            if len(self.closes) >= 10 and self.closes[-1] < np.mean(self.closes[-10:]):
                patterns.append({
                    "name": "倒锤子线",
                    "signal": "bullish",
                    "desc": "下跌趋势中出现倒锤子，关注次日确认",
                    "reliability": "low"
                })

        # 4. 大阳线
        if last["close"] > last["open"]:
            body_pct = (last["close"] - last["open"]) / last["open"] * 100 if last["open"] > 0 else 0
            if body_pct > 3:
                patterns.append({
                    "name": "大阳线",
                    "signal": "bullish",
                    "desc": f"实体涨幅{body_pct:.1f}%，多头力量强劲",
                    "reliability": "high"
                })

        # 5. 大阴线
        if last["close"] < last["open"]:
            body_pct = (last["open"] - last["close"]) / last["open"] * 100 if last["open"] > 0 else 0
            if body_pct > 3:
                patterns.append({
                    "name": "大阴线",
                    "signal": "bearish",
                    "desc": f"实体跌幅{body_pct:.1f}%，空头力量强劲",
                    "reliability": "high"
                })

        # 6. 看涨吞没（阳线完全包住前一根阴线）
        if prev and prev["close"] < prev["open"] and last["close"] > last["open"]:
            if last["open"] <= prev["close"] and last["close"] >= prev["open"]:
                patterns.append({
                    "name": "看涨吞没",
                    "signal": "bullish",
                    "desc": "阳线完全吞没前一根阴线，底部反转信号",
                    "reliability": "high"
                })

        # 7. 看跌吞没
        if prev and prev["close"] > prev["open"] and last["close"] < last["open"]:
            if last["open"] >= prev["close"] and last["close"] <= prev["open"]:
                patterns.append({
                    "name": "看跌吞没",
                    "signal": "bearish",
                    "desc": "阴线完全吞没前一根阳线，顶部反转信号",
                    "reliability": "high"
                })

        # 8. 早晨之星（三根K线组合）
        if len(self.kline_data) >= 3:
            k1, k2, k3 = self.kline_data[-3], self.kline_data[-2], self.kline_data[-1]
            if (k1["close"] < k1["open"] and  # 第一根大阴线
                abs(k2["close"] - k2["open"]) < abs(k1["close"] - k1["open"]) * 0.3 and  # 第二根小实体
                k3["close"] > k3["open"] and  # 第三根大阳线
                k3["close"] > (k1["open"] + k1["close"]) / 2):  # 阳线收盘超过第一根阴线实体中点
                patterns.append({
                    "name": "早晨之星",
                    "signal": "bullish",
                    "desc": "经典底部反转形态",
                    "reliability": "high"
                })

        # 9. 黄昏之星
        if len(self.kline_data) >= 3:
            k1, k2, k3 = self.kline_data[-3], self.kline_data[-2], self.kline_data[-1]
            if (k1["close"] > k1["open"] and
                abs(k2["close"] - k2["open"]) < abs(k1["close"] - k1["open"]) * 0.3 and
                k3["close"] < k3["open"] and
                k3["close"] < (k1["open"] + k1["close"]) / 2):
                patterns.append({
                    "name": "黄昏之星",
                    "signal": "bearish",
                    "desc": "经典顶部反转形态",
                    "reliability": "high"
                })

        # 10. 三连阳/三连阴
        if len(self.kline_data) >= 3:
            last3 = self.kline_data[-3:]
            if all(k["close"] > k["open"] for k in last3):
                patterns.append({
                    "name": "三连阳",
                    "signal": "bullish",
                    "desc": "连续三根阳线，多头趋势强劲",
                    "reliability": "medium"
                })
            elif all(k["close"] < k["open"] for k in last3):
                patterns.append({
                    "name": "三连阴",
                    "signal": "bearish",
                    "desc": "连续三根阴线，空头趋势强劲",
                    "reliability": "medium"
                })

        return patterns

    # ==================== 支撑阻力位 ====================

    def _calc_support_resistance(self) -> Dict:
        """计算支撑位和阻力位"""
        current_price = self.closes[-1]
        supports = []
        resistances = []

        # 1. 均线支撑/阻力
        ma_periods = [5, 10, 20, 60, 120]
        for p in ma_periods:
            if len(self.closes) >= p:
                ma_val = float(self._sma(self.closes, p)[-1])
                if ma_val < current_price:
                    supports.append({"price": round(ma_val, 2), "type": f"MA{p}", "strength": "medium"})
                else:
                    resistances.append({"price": round(ma_val, 2), "type": f"MA{p}", "strength": "medium"})

        # 2. 布林带支撑/阻力（使用缓存）
        boll = self._boll_result
        if "upper" in boll:
            if boll["lower"] < current_price:
                supports.append({"price": boll["lower"], "type": "BOLL下轨", "strength": "strong"})
            if boll["upper"] > current_price:
                resistances.append({"price": boll["upper"], "type": "BOLL上轨", "strength": "strong"})

        # 3. 近期高低点
        lookback = min(60, len(self.closes))
        recent_high = float(np.max(self.highs[-lookback:]))
        recent_low = float(np.min(self.lows[-lookback:]))
        mid_point = (recent_high + recent_low) / 2

        if recent_low < current_price:
            supports.append({"price": round(recent_low, 2), "type": "近期低点", "strength": "strong"})
        if recent_high > current_price:
            resistances.append({"price": round(recent_high, 2), "type": "近期高点", "strength": "strong"})

        # 4. 整数关口
        round_price = round(current_price / 5) * 5
        for delta in [-5, 0, 5, 10]:
            level = round_price + delta
            if level > 0 and level != current_price:
                if level < current_price:
                    supports.append({"price": level, "type": "整数关口", "strength": "weak"})
                else:
                    resistances.append({"price": level, "type": "整数关口", "strength": "weak"})

        # 去重并排序
        supports = sorted(self._dedupe_levels(supports), key=lambda x: x["price"], reverse=True)[:5]
        resistances = sorted(self._dedupe_levels(resistances), key=lambda x: x["price"])[:5]

        return {
            "supports": supports,
            "resistances": resistances,
            "current_price": round(float(current_price), 2),
        }

    def _dedupe_levels(self, levels: List[Dict]) -> List[Dict]:
        """去重相近价位（距离<1%视为同一价位）"""
        if not levels:
            return levels
        result = []
        for level in levels:
            is_dup = False
            for r in result:
                if abs(level["price"] - r["price"]) / r["price"] < 0.01:
                    is_dup = True
                    break
            if not is_dup:
                result.append(level)
        return result

    # ==================== 综合买卖信号 ====================

    def _generate_signals(self) -> Dict:
        """综合多指标生成买卖信号"""
        bullish_signals = []
        bearish_signals = []
        neutral_signals = []

        # 1. 均线信号
        ma = self._ma_result
        if ma["arrangement"] == "bullish":
            bullish_signals.append("均线多头排列")
        elif ma["arrangement"] == "bearish":
            bearish_signals.append("均线空头排列")

        for cross in ma.get("crosses", []):
            if cross["type"] == "golden":
                bullish_signals.append(cross["desc"])
            else:
                bearish_signals.append(cross["desc"])

        # 2. MACD信号
        macd = self._macd_result
        if macd["golden_cross"]:
            bullish_signals.append("MACD金叉")
        if macd["death_cross"]:
            bearish_signals.append("MACD死叉")
        if macd.get("divergence", {}).get("bottom_divergence"):
            bullish_signals.append("MACD底背离")
        if macd.get("divergence", {}).get("top_divergence"):
            bearish_signals.append("MACD顶背离")

        # 3. KDJ信号
        kdj = self._kdj_result
        if kdj["golden_cross"] and kdj["zone"] != "overbought":
            bullish_signals.append("KDJ金叉")
        if kdj["death_cross"] and kdj["zone"] != "oversold":
            bearish_signals.append("KDJ死叉")
        if kdj["zone"] == "oversold":
            bullish_signals.append("KDJ超卖区")
        if kdj["zone"] == "overbought":
            bearish_signals.append("KDJ超买区")

        # 4. RSI信号
        rsi = self._rsi_result
        if rsi["zone"] == "oversold":
            bullish_signals.append("RSI超卖")
        if rsi["zone"] == "overbought":
            bearish_signals.append("RSI超买")

        # 5. 布林带信号
        boll = self._boll_result
        if boll.get("position") == "below_lower":
            bullish_signals.append("价格触及布林下轨")
        if boll.get("position") == "above_upper":
            bearish_signals.append("价格触及布林上轨")

        # 6. 量价信号
        vol = self._volume_result
        if vol.get("coordination") == "price_vol_up":
            bullish_signals.append("量价齐升")
        if vol.get("coordination") == "price_down_vol_up":
            bearish_signals.append("放量下跌")

        # 7. K线形态信号
        patterns = self._patterns_result
        for p in patterns:
            if p["signal"] == "bullish":
                bullish_signals.append(f"K线形态: {p['name']}")
            elif p["signal"] == "bearish":
                bearish_signals.append(f"K线形态: {p['name']}")

        # 综合判断
        score = len(bullish_signals) - len(bearish_signals)
        if score >= 3:
            action = "strong_buy"
            desc = "多指标共振看多，建议积极买入"
        elif score >= 1:
            action = "buy"
            desc = "偏多信号较多，可考虑买入"
        elif score <= -3:
            action = "strong_sell"
            desc = "多指标共振看空，建议减仓/卖出"
        elif score <= -1:
            action = "sell"
            desc = "偏空信号较多，建议谨慎"
        else:
            action = "hold"
            desc = "多空信号均衡，建议观望"

        return {
            "action": action,
            "description": desc,
            "bullish_count": len(bullish_signals),
            "bearish_count": len(bearish_signals),
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals,
            "score": score,
        }

    # ==================== 技术面评分 ====================

    def _calc_technical_score(self) -> Dict:
        """技术面综合评分 0-100"""
        score = 0
        details = {}

        # 1. 均线排列 (20分)
        ma = self._ma_result
        if ma["arrangement"] == "bullish":
            ma_score = 20
        elif ma["arrangement"] == "mixed" and ma["above_ma_count"] >= 3:
            ma_score = 14
        elif ma["arrangement"] == "mixed":
            ma_score = 10
        else:
            ma_score = 4
        score += ma_score
        details["ma_score"] = ma_score

        # 2. MACD (20分)
        macd = self._macd_result
        macd_score = 10  # 基础分
        if macd["dif"] > 0:
            macd_score += 3
        if macd["golden_cross"]:
            macd_score += 5
        if macd["death_cross"]:
            macd_score -= 3
        if macd["histogram_trend"] == "expanding" and macd["dif"] > 0:
            macd_score += 2
        if macd.get("divergence", {}).get("bottom_divergence"):
            macd_score += 3
        if macd.get("divergence", {}).get("top_divergence"):
            macd_score -= 3
        macd_score = max(0, min(20, macd_score))
        score += macd_score
        details["macd_score"] = macd_score

        # 3. KDJ (15分)
        kdj = self._kdj_result
        kdj_score = 7
        if kdj["golden_cross"]:
            kdj_score += 5
        if kdj["zone"] == "oversold":
            kdj_score += 3
        if kdj["death_cross"]:
            kdj_score -= 3
        if kdj["zone"] == "overbought":
            kdj_score -= 3
        kdj_score = max(0, min(15, kdj_score))
        score += kdj_score
        details["kdj_score"] = kdj_score

        # 4. RSI (15分)
        rsi = self._rsi_result
        rsi6 = rsi["values"].get("rsi6", 50)
        if 40 <= rsi6 <= 60:
            rsi_score = 10
        elif 30 <= rsi6 < 40 or 60 < rsi6 <= 70:
            rsi_score = 12
        elif rsi6 < 30:
            rsi_score = 14  # 超卖反弹机会
        elif rsi6 > 70:
            rsi_score = 6  # 超买风险
        else:
            rsi_score = 8
        score += rsi_score
        details["rsi_score"] = rsi_score

        # 5. 布林带位置 (10分)
        boll = self._boll_result
        pb = boll.get("pb", 0.5)
        if 0.2 <= pb <= 0.5:
            boll_score = 8  # 中下轨区间，有上涨空间
        elif 0.5 < pb <= 0.8:
            boll_score = 6
        elif pb < 0.2:
            boll_score = 10  # 触及下轨，可能反弹
        else:
            boll_score = 4  # 触及上轨，可能回落
        score += boll_score
        details["boll_score"] = boll_score

        # 6. 量价配合 (10分)
        vol = self._volume_result
        if vol.get("coordination") == "price_vol_up":
            vol_score = 10
        elif vol.get("coordination") == "price_vol_down":
            vol_score = 5  # 缩量下跌可能是洗盘
        elif vol.get("coordination") == "price_up_vol_down":
            vol_score = 4
        elif vol.get("coordination") == "price_down_vol_up":
            vol_score = 2
        else:
            vol_score = 5
        score += vol_score
        details["volume_score"] = vol_score

        # 7. K线形态加减分 (10分)
        patterns = self._patterns_result
        pattern_score = 5
        for p in patterns:
            if p["signal"] == "bullish":
                reliability_bonus = {"high": 3, "medium": 2, "low": 1}.get(p.get("reliability", "low"), 1)
                pattern_score += reliability_bonus
            elif p["signal"] == "bearish":
                reliability_penalty = {"high": 3, "medium": 2, "low": 1}.get(p.get("reliability", "low"), 1)
                pattern_score -= reliability_penalty
        pattern_score = max(0, min(10, pattern_score))
        score += pattern_score
        details["pattern_score"] = pattern_score

        return {
            "total": round(score, 1),
            "rating": self._score_to_rating(score),
            "details": details,
        }

    def _score_to_rating(self, score: float) -> str:
        if score >= 80:
            return "强势"
        elif score >= 60:
            return "偏多"
        elif score >= 40:
            return "中性"
        elif score >= 20:
            return "偏空"
        else:
            return "弱势"

    # ==================== 工具函数 ====================

    def _sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """简单移动平均 (返回与data等长数组，前period-1个元素为NaN)"""
        if len(data) < period:
            return np.array([])
        result = np.full(len(data), np.nan)
        cumsum = np.cumsum(data)
        result[period - 1] = cumsum[period - 1] / period
        if len(data) > period:
            result[period:] = (cumsum[period:] - cumsum[:-period]) / period
        return result

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """指数移动平均"""
        ema = np.zeros(len(data))
        ema[0] = data[0]
        multiplier = 2 / (period + 1)
        for i in range(1, len(data)):
            ema[i] = data[i] * multiplier + ema[i - 1] * (1 - multiplier)
        return ema

    def _rolling_std(self, data: np.ndarray, period: int) -> np.ndarray:
        """滚动标准差"""
        result = np.zeros(len(data))
        for i in range(period - 1, len(data)):
            result[i] = np.std(data[i - period + 1:i + 1])
        return result

    def _now(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
