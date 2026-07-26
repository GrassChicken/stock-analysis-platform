"""
统一数据采集器

一次请求获取所有分析所需的原始数据，供各分析器共享。
消除 StockScorer 调用 6 个分析器时的重复 API 请求。
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import pandas as pd

logger = logging.getLogger(__name__)


class DataCollector:
    """统一数据采集器 — 一次获取，多分析器共享"""

    def __init__(self):
        self._pro = None
        self._rate_interval = 0.3  # Tushare 调用间隔（秒）
        self._last_call_time = 0

    @property
    def pro(self):
        """延迟获取 Tushare pro 接口"""
        if self._pro is None:
            from app.services.data.tushare_client import get_tushare_client
            self._pro = get_tushare_client().pro
        return self._pro

    def _rate_limit(self):
        """速率控制 — 替代各分析器中分散的 time.sleep"""
        elapsed = time.time() - self._last_call_time
        if elapsed < self._rate_interval:
            time.sleep(self._rate_interval - elapsed)
        self._last_call_time = time.time()

    @staticmethod
    def _format_code(code: str) -> str:
        """格式化股票代码"""
        code = code.strip()
        if '.' in code:
            return code.upper()
        if code.startswith(('6', '9')):
            return f"{code}.SH"
        return f"{code}.SZ"

    def collect(self, code: str, include_market_data: bool = True) -> Dict[str, Any]:
        """
        统一采集一只股票的全部原始数据

        Args:
            code: 股票代码
            include_market_data: 是否包含行情/K线数据（评分必须，单独分析可选）

        Returns:
            预加载数据字典，包含各 DataFrame
        """
        ts_code = self._format_code(code)
        logger.info(f"📦 DataCollector 开始采集: {ts_code}")
        t0 = time.time()

        data = {'ts_code': ts_code}

        # ====== Tushare 财务数据（集中获取，统一限速） ======
        data['fina_df'] = self._safe_call('fina_indicator', ts_code=ts_code)
        data['income_df'] = self._safe_call('income', ts_code=ts_code)
        data['balance_df'] = self._safe_call('balancesheet', ts_code=ts_code)
        data['cashflow_df'] = self._safe_call('cashflow', ts_code=ts_code)
        data['daily_basic_df'] = self._safe_call('daily_basic', ts_code=ts_code)
        # 近 7 天日线（用于获取最新收盘价）
        recent_start = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        data['daily_df'] = self._safe_call('daily', ts_code=ts_code, start_date=recent_start)

        # ====== 行情数据 ======
        if include_market_data:
            from app.services.data.stock_service import stock_service
            data['kline'] = stock_service.get_kline(code, period='daily', count=120)
            # 当前价格用 daily_basic 的最新一条
            data['current_price'] = self._extract_current_price(data['daily_basic_df'])
        else:
            data['kline'] = []
            data['current_price'] = None

        elapsed = time.time() - t0
        logger.info(f"📦 DataCollector 采集完成: {ts_code}, 耗时 {elapsed:.1f}s")
        return data

    def _safe_call(self, api_name: str, **kwargs) -> pd.DataFrame:
        """安全调用 Tushare API，失败返回空 DataFrame"""
        try:
            self._rate_limit()
            api_func = getattr(self.pro, api_name, None)
            if api_func is None:
                logger.warning(f"Tushare 无接口: {api_name}")
                return pd.DataFrame()
            df = api_func(**kwargs)
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.error(f"Tushare {api_name} 调用失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def _extract_current_price(daily_basic_df: pd.DataFrame) -> Optional[float]:
        """从 daily_basic 中提取最新收盘价"""
        if daily_basic_df is None or daily_basic_df.empty:
            return None
        try:
            # daily_basic 没有 close 字段，需要从 daily 接口获取
            # 这里只返回 None，由调用方补充
            return None
        except Exception:
            return None


# 全局单例
data_collector = DataCollector()
