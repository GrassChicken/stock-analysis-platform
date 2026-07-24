"""
AKShare 补充数据客户端

提供资金流向、北向资金、融资融券等数据
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None
    logging.warning("AKShare 未安装，相关功能不可用")

from app.services.data.cache_manager import cached, cache_get, cache_set, CACHE_TTL

logger = logging.getLogger(__name__)


class AKShareClient:
    """AKShare 补充数据客户端"""

    def __init__(self):
        if ak is None:
            logger.warning("AKShare 未安装，资金流向等功能不可用")

    def get_money_flow(self, code: str) -> Dict[str, Any]:
        """
        获取个股资金流向（主力/超大单/大单/中单/小单）
        
        Args:
            code: 股票代码（6位数字）
        
        Returns:
            资金流向字典
        """
        if ak is None:
            return {}

        code = code.strip()
        if '.' in code:
            code = code.split('.')[0]
        
        # 检查缓存
        cache_key = f"akshare:money_flow:{code}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            # 使用 stock_individual_fund_flow_rank 获取所有股票今日资金流向排名
            df = ak.stock_individual_fund_flow_rank(indicator="今日")
            
            if df.empty:
                logger.warning(f"个股资金流向数据为空")
                return {}
            
            # 筛选指定股票
            stock_data = df[df['代码'] == code]
            
            if stock_data.empty:
                logger.warning(f"未找到 {code} 的资金流向数据")
                return {}
            
            latest = stock_data.iloc[0]
            
            result = {
                'code': code,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'close': self._safe_float(latest.get('最新价')),
                'change_pct': self._safe_float(latest.get('涨跌幅')),
                # 主力
                'main_net_inflow': self._safe_float(latest.get('主力净流入-净额')),
                'main_net_inflow_pct': self._safe_float(latest.get('主力净流入-净占比')),
                # 超大单
                'super_large_net': self._safe_float(latest.get('超大单净流入-净额')),
                'super_large_net_pct': self._safe_float(latest.get('超大单净流入-净占比')),
                # 大单
                'large_net': self._safe_float(latest.get('大单净流入-净额')),
                'large_net_pct': self._safe_float(latest.get('大单净流入-净占比')),
                # 中单
                'medium_net': self._safe_float(latest.get('中单净流入-净额')),
                'medium_net_pct': self._safe_float(latest.get('中单净流入-净占比')),
                # 小单
                'small_net': self._safe_float(latest.get('小单净流入-净额')),
                'small_net_pct': self._safe_float(latest.get('小单净流入-净占比')),
            }
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['akshare'])
            
            return result
        except Exception as e:
            logger.error(f"获取资金流向失败 {code}: {e}")
            return {}

    def get_north_flow(self) -> Dict[str, Any]:
        """
        获取北向资金流向
        
        Returns:
            北向资金流向字典
        """
        if ak is None:
            return {}

        # 检查缓存
        cache_key = "akshare:north_flow"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            # 获取沪股通历史数据
            df_sh = ak.stock_hsgt_hist_em(symbol="沪股通")
            df_sz = ak.stock_hsgt_hist_em(symbol="深股通")
            
            result = {
                'history': [],
                'latest': {}
            }
            
            # 沪股通最近10天
            if not df_sh.empty:
                for _, row in df_sh.tail(10).iterrows():
                    result['history'].append({
                        'date': str(row.get('日期', '')),
                        'net_inflow': self._safe_float(row.get('当日成交净买额')),
                        'market': '沪股通'
                    })
            
            # 深股通最近10天
            if not df_sz.empty:
                for _, row in df_sz.tail(10).iterrows():
                    result['history'].append({
                        'date': str(row.get('日期', '')),
                        'net_inflow': self._safe_float(row.get('当日成交净买额')),
                        'market': '深股通'
                    })
            
            # 按日期降序排列
            result['history'].sort(key=lambda x: x['date'], reverse=True)
            
            # 汇总最新一天的北向资金
            if result['history']:
                latest_date = result['history'][0]['date']
                latest_inflow = sum(
                    h['net_inflow'] for h in result['history'] if h['date'] == latest_date
                )
                result['latest'] = {
                    'date': latest_date,
                    'net_inflow': latest_inflow
                }
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['akshare'])
            
            return result
        except Exception as e:
            logger.error(f"获取北向资金流向失败: {e}")
            return {}

    def get_margin_detail(self, code: str) -> Dict[str, Any]:
        """
        获取融资融券数据
        
        Args:
            code: 股票代码（6位数字）
        
        Returns:
            融资融券数据字典
        """
        if ak is None:
            return {}

        code = code.strip()
        if '.' in code:
            code = code.split('.')[0]
        
        # 检查缓存
        cache_key = f"akshare:margin:{code}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            # 根据股票代码选择交易所
            if code.startswith('6'):
                # 上交所
                date_str = datetime.now().strftime('%Y%m%d')
                df = ak.stock_margin_detail_sse(date=date_str)
                code_col = '标的证券代码'
            else:
                # 深交所
                date_str = datetime.now().strftime('%Y%m%d')
                df = ak.stock_margin_detail_szse(date=date_str)
                code_col = '证券代码' if '证券代码' in df.columns else '标的证券代码'
            
            if df is None or df.empty:
                logger.warning(f"融资融券数据为空，日期: {date_str}")
                return {}
            
            # 查找代码列
            if code_col not in df.columns:
                # 尝试其他可能的列名
                for col in df.columns:
                    if '代码' in col:
                        code_col = col
                        break
                else:
                    logger.warning(f"融资融券数据列名: {df.columns.tolist()}，找不到代码列")
                    return {}
            
            # 筛选指定股票
            stock_data = df[df[code_col].astype(str) == code]
            
            if stock_data.empty:
                logger.warning(f"未找到 {code} 的融资融券数据")
                return {}
            
            latest = stock_data.iloc[0]
            
            # 尝试各种可能的列名
            result = {
                'code': code,
                'date': str(latest.get('日期', latest.get('信用交易日期', ''))),
                '融资余额': self._safe_float(self._find_col(latest, ['融资余额(元)', '融资余额'])),
                '融资买入额': self._safe_float(self._find_col(latest, ['融资买入额(元)', '融资买入额'])),
                '融资偿还额': self._safe_float(self._find_col(latest, ['融资偿还额(元)', '融资偿还额'])),
                '融资净买入': self._safe_float(self._find_col(latest, ['融资净买入额(元)', '融资净买入'])),
                '融券余量': self._safe_float(self._find_col(latest, ['融券余量(股)', '融券余量'])),
                '融券余额': self._safe_float(self._find_col(latest, ['融券余额(元)', '融券余额'])),
                '融券卖出量': self._safe_float(self._find_col(latest, ['融券卖出量(股)', '融券卖出量'])),
                '融券偿还量': self._safe_float(self._find_col(latest, ['融券偿还量(股)', '融券偿还量'])),
                '融券净卖出': self._safe_float(self._find_col(latest, ['融券净卖出量(股)', '融券净卖出量'])),
                '融资融券余额': self._safe_float(self._find_col(latest, ['融资融券余额(元)', '融资融券余额'])),
            }
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['akshare'])
            
            return result
        except Exception as e:
            logger.error(f"获取融资融券数据失败 {code}: {e}")
            return {}

    def _safe_float(self, value) -> float:
        """安全转换为 float"""
        if value is None:
            return 0.0
        try:
            val = float(value)
            return 0.0 if pd.isna(val) else val
        except (ValueError, TypeError):
            return 0.0

    def _find_col(self, row, candidates: list):
        """从候选列名中找第一个存在的列"""
        for col in candidates:
            if col in row.index:
                return row[col]
        return None


# 全局单例
akshare_client = AKShareClient()
