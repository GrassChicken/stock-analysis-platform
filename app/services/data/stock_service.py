"""
统一股票数据服务

提供 A 股数据获取能力，基于 Tushare
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import pandas as pd
from pypinyin import lazy_pinyin

from app.services.data.tushare_client import get_tushare_client
from app.services.data.cache_manager import cached, cache_get, cache_set, CACHE_TTL

logger = logging.getLogger(__name__)


class StockService:
    """统一股票数据服务"""

    def __init__(self):
        self._stock_list_cache = None
        self._stock_list_time = 0

    def _get_pro(self):
        """获取 Tushare pro 接口"""
        client = get_tushare_client()
        return client.pro

    def _format_code(self, code: str) -> str:
        """
        格式化股票代码
        000001 -> 000001.SZ
        600519 -> 600519.SH
        """
        code = code.strip().upper()
        if '.' in code:
            return code
        # 根据代码判断交易所
        if code.startswith(('6', '9')):
            return f"{code}.SH"
        else:
            return f"{code}.SZ"

    @cached('stock_list')
    def get_all_stocks(self) -> List[Dict[str, Any]]:
        """
        获取 A 股列表并缓存
        
        Returns:
            股票列表 [{code, name, industry, area, list_date}, ...]
        """
        pro = self._get_pro()
        if not pro:
            return []

        try:
            df = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,list_date,market'
            )
            time.sleep(0.3)  # 频率限制
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    'ts_code': row['ts_code'],
                    'code': row['symbol'],
                    'name': row['name'],
                    'area': row.get('area', ''),
                    'industry': row.get('industry', ''),
                    'list_date': row.get('list_date', ''),
                    'market': row.get('market', '')
                })
            
            logger.info(f"✓ 获取 {len(result)} 只股票")
            return result
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    def search_stock(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索股票（支持代码/名称/拼音首字母）
        
        Args:
            keyword: 搜索关键词
        
        Returns:
            匹配的股票列表
        """
        keyword = keyword.strip().upper()
        if not keyword:
            return []

        stocks = self.get_all_stocks()
        results = []
        
        for stock in stocks:
            # 代码匹配
            if keyword in stock['code'] or keyword in stock['ts_code']:
                results.append(stock)
                continue
            
            # 名称匹配
            if keyword in stock['name'].upper():
                results.append(stock)
                continue
            
            # 拼音首字母匹配
            pinyin_initials = ''.join([p[0] for p in lazy_pinyin(stock['name'])]).upper()
            if keyword in pinyin_initials:
                results.append(stock)
                continue
            
            # 限制结果数量
            if len(results) >= 50:
                break
        
        return results

    def get_quote(self, code: str) -> Dict[str, Any]:
        """
        获取最新行情
        
        Args:
            code: 股票代码（支持 000001 或 000001.SZ）
        
        Returns:
            行情字典
        """
        ts_code = self._format_code(code)
        
        # 检查缓存
        cache_key = f"quote:{ts_code}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        pro = self._get_pro()
        if not pro:
            return {}

        try:
            # 获取最近交易日行情
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            
            df = pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            time.sleep(0.3)  # 频率限制
            
            if df.empty:
                return {}
            
            # 取最新一条
            row = df.iloc[0]
            
            # 获取股票名称
            stock_info = self._get_stock_info(ts_code)
            
            result = {
                'ts_code': ts_code,
                'code': ts_code.split('.')[0],
                'name': stock_info.get('name', ''),
                'price': float(row.get('close', 0)),
                'open': float(row.get('open', 0)),
                'high': float(row.get('high', 0)),
                'low': float(row.get('low', 0)),
                'pre_close': float(row.get('pre_close', 0)),
                'change': float(row.get('close', 0) - row.get('pre_close', 0)),
                'change_pct': float((row.get('close', 0) - row.get('pre_close', 0)) / row.get('pre_close', 1) * 100),
                'vol': float(row.get('vol', 0)),
                'amount': float(row.get('amount', 0)),
                'trade_date': str(row.get('trade_date', '')),
            }
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['quote'])
            
            return result
        except Exception as e:
            logger.error(f"获取行情失败 {ts_code}: {e}")
            return {}

    def _get_stock_info(self, ts_code: str) -> Dict[str, Any]:
        """获取单只股票基本信息"""
        stocks = self.get_all_stocks()
        for stock in stocks:
            if stock['ts_code'] == ts_code:
                return stock
        return {}

    def get_kline(self, code: str, period: str = 'daily', count: int = 250) -> List[Dict[str, Any]]:
        """
        获取 K 线数据
        
        Args:
            code: 股票代码
            period: 周期 daily/weekly/monthly
            count: 数据条数
        
        Returns:
            K 线数据列表
        """
        ts_code = self._format_code(code)
        
        # 检查缓存
        cache_key = f"kline:{ts_code}:{period}:{count}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        pro = self._get_pro()
        if not pro:
            return []

        try:
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            if period == 'daily':
                start_date = (datetime.now() - timedelta(days=count * 2)).strftime('%Y%m%d')
            elif period == 'weekly':
                start_date = (datetime.now() - timedelta(weeks=count * 2)).strftime('%Y%m%d')
            else:  # monthly
                start_date = (datetime.now() - timedelta(days=count * 60)).strftime('%Y%m%d')
            
            df = pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            time.sleep(0.3)  # 频率限制
            
            if df.empty:
                return []
            
            # 根据周期进行数据聚合
            if period == 'weekly':
                df = self._aggregate_weekly(df)
            elif period == 'monthly':
                df = self._aggregate_monthly(df)
            
            # 只返回最近的 count 条
            df = df.head(count)
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    'ts_code': row['ts_code'],
                    'trade_date': str(row['trade_date']),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'pre_close': float(row.get('pre_close', 0)),
                    'change': float(row.get('change', 0)),
                    'pct_chg': float(row.get('pct_chg', 0)),
                    'vol': float(row['vol']),
                    'amount': float(row['amount']),
                })
            
            # 按日期升序
            result.reverse()
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['kline'])
            
            return result
        except Exception as e:
            logger.error(f"获取 K 线失败 {ts_code}: {e}")
            return []

    def _aggregate_weekly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将日K数据聚合为周K
        
        规则：
        - 按交易周分组
        - open: 周初开盘价
        - high: 周最高价
        - low: 周最低价
        - close: 周末收盘价
        - vol/amount: 累加
        - trade_date: 周末日期
        """
        if df.empty:
            return df
        
        # 确保 trade_date 是日期类型并排序（降序，最新在前）
        df = df.copy()
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date', ascending=False).reset_index(drop=True)
        
        # 按周分组（使用 ISO 周）
        df['week'] = df['trade_date'].dt.isocalendar().week.astype(int)
        df['year'] = df['trade_date'].dt.year
        
        result = []
        for (year, week), group in df.groupby(['year', 'week']):
            group = group.sort_values('trade_date', ascending=False)
            aggregated = {
                'ts_code': group.iloc[0]['ts_code'],
                'trade_date': group.iloc[0]['trade_date'],  # 周末日期
                'open': group.iloc[-1]['open'],  # 周初开盘（最早一天的开盘）
                'high': group['high'].max(),
                'low': group['low'].min(),
                'close': group.iloc[0]['close'],  # 周末收盘（最新一天的收盘）
                'vol': group['vol'].sum(),
                'amount': group['amount'].sum(),
            }
            result.append(aggregated)
        
        result_df = pd.DataFrame(result)
        # 按日期降序排列（最新在前），与日线数据保持一致
        result_df = result_df.sort_values('trade_date', ascending=False).reset_index(drop=True)
        result_df['trade_date'] = result_df['trade_date'].dt.strftime('%Y%m%d')
        return result_df

    def _aggregate_monthly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将日K数据聚合为月K
        
        规则：
        - 按交易月分组
        - open: 月初开盘价
        - high: 月最高价
        - low: 月最低价
        - close: 月末收盘价
        - vol/amount: 累加
        - trade_date: 月末日期
        """
        if df.empty:
            return df
        
        # 确保 trade_date 是日期类型并排序（降序，最新在前）
        df = df.copy()
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date', ascending=False).reset_index(drop=True)
        
        # 按月分组
        df['year'] = df['trade_date'].dt.year
        df['month'] = df['trade_date'].dt.month
        
        result = []
        for (year, month), group in df.groupby(['year', 'month']):
            group = group.sort_values('trade_date', ascending=False)
            aggregated = {
                'ts_code': group.iloc[0]['ts_code'],
                'trade_date': group.iloc[0]['trade_date'],  # 月末日期
                'open': group.iloc[-1]['open'],  # 月初开盘（最早一天的开盘）
                'high': group['high'].max(),
                'low': group['low'].min(),
                'close': group.iloc[0]['close'],  # 月末收盘（最新一天的收盘）
                'vol': group['vol'].sum(),
                'amount': group['amount'].sum(),
            }
            result.append(aggregated)
        
        result_df = pd.DataFrame(result)
        # 按日期降序排列（最新在前），与日线数据保持一致
        result_df = result_df.sort_values('trade_date', ascending=False).reset_index(drop=True)
        result_df['trade_date'] = result_df['trade_date'].dt.strftime('%Y%m%d')
        return result_df

    def get_daily_basic(self, code: str) -> Dict[str, Any]:
        """
        获取每日基本指标（PE/PB/市值/换手率等）
        
        Args:
            code: 股票代码
        
        Returns:
            指标字典
        """
        ts_code = self._format_code(code)
        
        # 检查缓存
        cache_key = f"daily_basic:{ts_code}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        pro = self._get_pro()
        if not pro:
            return {}

        try:
            # 获取最近交易日
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            
            df = pro.daily_basic(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,total_mv,circ_mv'
            )
            time.sleep(0.3)  # 频率限制
            
            if df.empty:
                return {}
            
            row = df.iloc[0]
            
            result = {
                'ts_code': ts_code,
                'trade_date': str(row.get('trade_date', '')),
                'turnover_rate': float(row.get('turnover_rate', 0) or 0),
                'volume_ratio': float(row.get('volume_ratio', 0) or 0),
                'pe': float(row.get('pe', 0) or 0),
                'pe_ttm': float(row.get('pe_ttm', 0) or 0),
                'pb': float(row.get('pb', 0) or 0),
                'ps': float(row.get('ps', 0) or 0),
                'ps_ttm': float(row.get('ps_ttm', 0) or 0),
                'dv_ratio': float(row.get('dv_ratio', 0) or 0),
                'dv_ttm': float(row.get('dv_ttm', 0) or 0),
                'total_share': float(row.get('total_share', 0) or 0),
                'float_share': float(row.get('float_share', 0) or 0),
                'total_mv': float(row.get('total_mv', 0) or 0),
                'circ_mv': float(row.get('circ_mv', 0) or 0),
            }
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['daily_basic'])
            
            return result
        except Exception as e:
            logger.error(f"获取每日指标失败 {ts_code}: {e}")
            return {}


# 全局单例
stock_service = StockService()
