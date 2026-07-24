"""
AKShare 补充数据客户端

提供资金流向、北向资金、融资融券等数据
数据源：东方财富/新浪（通过 AKShare）
所有接口加 try/except 防崩溃，失败返回空字典/列表
"""
import logging
from typing import Dict, Any
from datetime import datetime

import pandas as pd

try:
    import akshare as ak
except ImportError:
    ak = None
    logging.warning("AKShare 未安装，相关功能不可用")

from app.services.data.cache_manager import cache_get, cache_set, CACHE_TTL

logger = logging.getLogger(__name__)


class AKShareClient:
    """AKShare 补充数据客户端"""

    def get_money_flow(self, code: str) -> Dict[str, Any]:
        """
        获取个股资金流向（主力/超大单/大单/中单/小单）
        
        Args:
            code: 股票代码（6位数字或带后缀）
        
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
            # 方案1: 使用 stock_individual_fund_flow（逐股查询，新浪源）
            try:
                market = "sh" if code.startswith('6') else "sz"
                df = ak.stock_individual_fund_flow(stock=code, market=market)
                
                if df is not None and not df.empty:
                    latest = df.iloc[-1]  # 最后一行是最新
                    
                    result = self._parse_fund_flow_row(latest, code)
                    cache_set(cache_key, result, timeout=CACHE_TTL['akshare'])
                    return result
            except Exception as e:
                logger.warning(f"stock_individual_fund_flow 失败: {e}, 尝试备选方案")
            
            # 方案2: 使用 stock_individual_fund_flow_rank（全量排名，东方财富源）
            try:
                df = ak.stock_individual_fund_flow_rank(indicator="今日")
                if df is not None and not df.empty:
                    stock_data = df[df['代码'] == code]
                    if not stock_data.empty:
                        latest = stock_data.iloc[0]
                        result = {
                            'code': code,
                            'date': datetime.now().strftime('%Y-%m-%d'),
                            'close': self._safe_float(latest.get('最新价')),
                            'change_pct': self._safe_float(latest.get('涨跌幅')),
                            'main_net_inflow': self._safe_float(latest.get('主力净流入-净额')),
                            'main_net_inflow_pct': self._safe_float(latest.get('主力净流入-净占比')),
                            'super_large_net': self._safe_float(latest.get('超大单净流入-净额')),
                            'super_large_net_pct': self._safe_float(latest.get('超大单净流入-净占比')),
                            'large_net': self._safe_float(latest.get('大单净流入-净额')),
                            'large_net_pct': self._safe_float(latest.get('大单净流入-净占比')),
                            'medium_net': self._safe_float(latest.get('中单净流入-净额')),
                            'medium_net_pct': self._safe_float(latest.get('中单净流入-净占比')),
                            'small_net': self._safe_float(latest.get('小单净流入-净额')),
                            'small_net_pct': self._safe_float(latest.get('小单净流入-净占比')),
                        }
                        cache_set(cache_key, result, timeout=CACHE_TTL['akshare'])
                        return result
            except Exception as e:
                logger.warning(f"stock_individual_fund_flow_rank 也失败: {e}")
            
            return {}
        except Exception as e:
            logger.error(f"获取资金流向失败 {code}: {e}")
            return {}

    def _parse_fund_flow_row(self, row, code: str) -> Dict[str, Any]:
        """解析 stock_individual_fund_flow 返回的行数据"""
        result = {
            'code': code,
            'date': str(row.get('日期', datetime.now().strftime('%Y-%m-%d'))),
            'close': self._safe_float(row.get('收盘价')),
            'change_pct': self._safe_float(row.get('涨跌幅')),
        }
        
        # 新浪源的列名映射
        flow_cols = {
            'main_net_inflow': ['主力净流入-净额', '主力净流入'],
            'main_net_inflow_pct': ['主力净流入-净占比'],
            'super_large_net': ['超大单净流入-净额', '超大单净流入'],
            'super_large_net_pct': ['超大单净流入-净占比'],
            'large_net': ['大单净流入-净额', '大单净流入'],
            'large_net_pct': ['大单净流入-净占比'],
            'medium_net': ['中单净流入-净额', '中单净流入'],
            'medium_net_pct': ['中单净流入-净占比'],
            'small_net': ['小单净流入-净额', '小单净流入'],
            'small_net_pct': ['小单净流入-净占比'],
        }
        
        for key, candidates in flow_cols.items():
            val = None
            for col in candidates:
                if col in row.index:
                    val = self._safe_float(row[col])
                    break
            result[key] = val if val is not None else 0.0
        
        return result

    def get_north_flow(self) -> Dict[str, Any]:
        """
        获取北向资金流向（沪股通+深股通）
        
        Returns:
            北向资金流向字典
        """
        if ak is None:
            return {}

        cache_key = "akshare:north_flow"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            result = {
                'history': [],
                'latest': {},
                'sh': [],
                'sz': []
            }
            
            # 沪股通
            try:
                df_sh = ak.stock_hsgt_hist_em(symbol="沪股通")
                if df_sh is not None and not df_sh.empty:
                    # 过滤掉 NaN 数据
                    df_sh = df_sh.dropna(subset=['当日成交净买额'])
                    for _, row in df_sh.tail(10).iterrows():
                        item = {
                            'date': str(row.get('日期', '')),
                            'net_inflow': self._safe_float(row.get('当日成交净买额')),
                            'buy_amount': self._safe_float(row.get('买入成交额')),
                            'sell_amount': self._safe_float(row.get('卖出成交额')),
                        }
                        result['history'].append({**item, 'market': '沪股通'})
                        result['sh'].append(item)
            except Exception as e:
                logger.warning(f"获取沪股通数据失败: {e}")
            
            # 深股通
            try:
                df_sz = ak.stock_hsgt_hist_em(symbol="深股通")
                if df_sz is not None and not df_sz.empty:
                    df_sz = df_sz.dropna(subset=['当日成交净买额'])
                    for _, row in df_sz.tail(10).iterrows():
                        item = {
                            'date': str(row.get('日期', '')),
                            'net_inflow': self._safe_float(row.get('当日成交净买额')),
                            'buy_amount': self._safe_float(row.get('买入成交额')),
                            'sell_amount': self._safe_float(row.get('卖出成交额')),
                        }
                        result['history'].append({**item, 'market': '深股通'})
                        result['sz'].append(item)
            except Exception as e:
                logger.warning(f"获取深股通数据失败: {e}")
            
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
            
            cache_set(cache_key, result, timeout=CACHE_TTL['akshare'])
            return result
        except Exception as e:
            logger.error(f"获取北向资金流向失败: {e}")
            return {}

    def get_margin_detail(self, code: str) -> Dict[str, Any]:
        """
        获取融资融券数据
        
        Args:
            code: 股票代码（6位数字或带后缀）
        
        Returns:
            融资融券数据字典
        """
        if ak is None:
            return {}

        code = code.strip()
        if '.' in code:
            code = code.split('.')[0]
        
        cache_key = f"akshare:margin:{code}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        try:
            # 根据股票代码选择交易所
            df = None
            if code.startswith('6'):
                # 上交所
                try:
                    date_str = datetime.now().strftime('%Y%m%d')
                    df = ak.stock_margin_detail_sse(date=date_str)
                except Exception:
                    # 尝试前一交易日
                    from datetime import timedelta
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                    df = ak.stock_margin_detail_sse(date=yesterday)
            else:
                # 深交所
                try:
                    date_str = datetime.now().strftime('%Y%m%d')
                    df = ak.stock_margin_detail_szse(date=date_str)
                except Exception:
                    from datetime import timedelta
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
                    df = ak.stock_margin_detail_szse(date=yesterday)
            
            if df is None or df.empty:
                logger.warning(f"融资融券数据为空，代码: {code}")
                return {}
            
            # 查找代码列
            code_col = None
            for col in df.columns:
                if '代码' in str(col):
                    code_col = col
                    break
            
            if code_col is None:
                logger.warning(f"融资融券数据找不到代码列，列名: {df.columns.tolist()}")
                return {}
            
            # 筛选指定股票
            df[code_col] = df[code_col].astype(str).str.strip()
            stock_data = df[df[code_col] == code]
            
            if stock_data.empty:
                logger.warning(f"未找到 {code} 的融资融券数据")
                return {}
            
            latest = stock_data.iloc[0]
            
            # 动态匹配列名
            result = {
                'code': code,
                'date': str(self._find_col_val(latest, ['日期', '信用交易日期', '交易日期'])),
                '融资余额': self._safe_float(self._find_col_val(latest, ['融资余额(元)', '融资余额', '融资余额(万元)'])),
                '融资买入额': self._safe_float(self._find_col_val(latest, ['融资买入额(元)', '融资买入额', '融资买入额(万元)'])),
                '融资偿还额': self._safe_float(self._find_col_val(latest, ['融资偿还额(元)', '融资偿还额', '融资偿还额(万元)'])),
                '融资净买入': self._safe_float(self._find_col_val(latest, ['融资净买入额(元)', '融资净买入', '融资净买入额(万元)'])),
                '融券余量': self._safe_float(self._find_col_val(latest, ['融券余量(股)', '融券余量', '融券余量(万股)'])),
                '融券余额': self._safe_float(self._find_col_val(latest, ['融券余额(元)', '融券余额', '融券余额(万元)'])),
                '融券卖出量': self._safe_float(self._find_col_val(latest, ['融券卖出量(股)', '融券卖出量', '融券卖出量(万股)'])),
                '融券偿还量': self._safe_float(self._find_col_val(latest, ['融券偿还量(股)', '融券偿还量', '融券偿还量(万股)'])),
                '融券净卖出': self._safe_float(self._find_col_val(latest, ['融券净卖出量(股)', '融券净卖出量', '融券净卖出量(万股)'])),
                '融资融券余额': self._safe_float(self._find_col_val(latest, ['融资融券余额(元)', '融资融券余额', '融资融券余额(万元)'])),
            }
            
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

    def _find_col_val(self, row, candidates: list):
        """从候选列名中找第一个存在的值"""
        for col in candidates:
            if col in row.index:
                return row[col]
        return None


# 全局单例
akshare_client = AKShareClient()
