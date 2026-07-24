"""
Tushare 数据客户端

提供稳定的 A 股数据获取能力
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import tushare as ts
import pandas as pd

logger = logging.getLogger(__name__)


class TushareClient:
    """Tushare 数据客户端"""
    
    def __init__(self, token: str):
        self.token = token
        self.pro = None
        self._init_api()
    
    def _init_api(self):
        """初始化 Tushare API"""
        try:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            logger.info("✓ Tushare API 初始化成功")
        except Exception as e:
            logger.error(f"✗ Tushare API 初始化失败: {e}")
    
    def _format_code(self, code: str) -> str:
        """格式化股票代码为 Tushare 格式 (如 000001.SZ)"""
        code = code.strip()
        if '.' in code:
            return code.upper()
        
        # 根据代码判断交易所
        if code.startswith(('6', '9')):
            return f"{code}.SH"
        else:
            return f"{code}.SZ"
    
    def get_stock_basic(self, exchange: str = '', list_status: str = 'L') -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            exchange: 交易所 SSE=上交所 SZSE=深交所 ''=全部
            list_status: L=上市 D=退市 P=暂停
        
        Returns:
            股票列表 DataFrame
        """
        if not self.pro:
            return pd.DataFrame()
        
        try:
            df = self.pro.stock_basic(
                exchange=exchange,
                list_status=list_status,
                fields='ts_code,symbol,name,area,industry,list_date'
            )
            logger.info(f"✓ 获取 {len(df)} 只股票")
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_daily(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取日线行情
        
        Args:
            ts_code: 股票代码（如 000001.SZ）
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
        
        Returns:
            日线数据 DataFrame
        """
        if not self.pro:
            return pd.DataFrame()
        
        ts_code = self._format_code(ts_code)
        
        try:
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            return pd.DataFrame()
    
    def get_daily_basic(self, ts_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取每日指标（PE/PB/换手率等）
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            每日指标 DataFrame
        """
        if not self.pro:
            return pd.DataFrame()
        
        ts_code = self._format_code(ts_code)
        
        try:
            df = self.pro.daily_basic(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,turnover_rate,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,total_mv,circ_mv'
            )
            return df
        except Exception as e:
            logger.error(f"获取每日指标失败: {e}")
            return pd.DataFrame()
    
    def get_income(self, ts_code: str, period: str = None) -> pd.DataFrame:
        """
        获取利润表
        
        Args:
            ts_code: 股票代码
            period: 报告期（如 20231231）
        
        Returns:
            利润表 DataFrame
        """
        if not self.pro:
            return pd.DataFrame()
        
        ts_code = self._format_code(ts_code)
        
        try:
            df = self.pro.income(
                ts_code=ts_code,
                period=period,
                fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps,total_revenue,revenue,total_cogs,oper_cost,operate_profit,total_profit,n_income,n_income_attr_p'
            )
            return df
        except Exception as e:
            logger.error(f"获取利润表失败: {e}")
            return pd.DataFrame()
    
    def get_balancesheet(self, ts_code: str, period: str = None) -> pd.DataFrame:
        """
        获取资产负债表
        
        Args:
            ts_code: 股票代码
            period: 报告期
        
        Returns:
            资产负债表 DataFrame
        """
        if not self.pro:
            return pd.DataFrame()
        
        ts_code = self._format_code(ts_code)
        
        try:
            df = self.pro.balancesheet(
                ts_code=ts_code,
                period=period,
                fields='ts_code,end_date,report_type,total_assets,total_liab,total_hldr_eqy_exc_min_int,total_hldr_eqy_inc_min_int'
            )
            return df
        except Exception as e:
            logger.error(f"获取资产负债表失败: {e}")
            return pd.DataFrame()
    
    def get_cashflow(self, ts_code: str, period: str = None) -> pd.DataFrame:
        """
        获取现金流量表
        
        Args:
            ts_code: 股票代码
            period: 报告期
        
        Returns:
            现金流量表 DataFrame
        """
        if not self.pro:
            return pd.DataFrame()
        
        ts_code = self._format_code(ts_code)
        
        try:
            df = self.pro.cashflow(
                ts_code=ts_code,
                period=period,
                fields='ts_code,end_date,report_type,n_cashflow_act,n_cashflow_inv_act,n_cash_flows_fnc_act'
            )
            return df
        except Exception as e:
            logger.error(f"获取现金流量表失败: {e}")
            return pd.DataFrame()
    
    def get_fina_indicator(self, ts_code: str, period: str = None) -> pd.DataFrame:
        """
        获取财务指标数据
        
        Args:
            ts_code: 股票代码
            period: 报告期
        
        Returns:
            财务指标 DataFrame
        """
        if not self.pro:
            return pd.DataFrame()
        
        ts_code = self._format_code(ts_code)
        
        try:
            df = self.pro.fina_indicator(
                ts_code=ts_code,
                period=period,
                fields='ts_code,end_date,eps,dt_eps,bps,roe,roe_waa,roe_dt,grossprofit_margin,netprofit_margin,op_yoy,dt_netprofit_yoy,tr_yoy,or_yoy,current_ratio,quick_ratio,debt_to_assets,assets_turn,fix_ass_ratio'
            )
            return df
        except Exception as e:
            logger.error(f"获取财务指标失败: {e}")
            return pd.DataFrame()
    
    def get_quote(self, ts_code: str) -> Dict[str, Any]:
        """
        获取实时行情
        
        Args:
            ts_code: 股票代码
        
        Returns:
            行情字典
        """
        if not self.pro:
            return {}
        
        ts_code = self._format_code(ts_code)
        
        try:
            # 获取最新交易日的行情
            today = datetime.now().strftime('%Y%m%d')
            df = self.pro.daily(ts_code=ts_code, start_date=today, end_date=today)
            
            if df.empty:
                # 如果今天没有数据，尝试获取最近一天
                df = self.pro.daily(ts_code=ts_code, start_date=today, end_date=today)
                if df.empty:
                    return {}
            
            row = df.iloc[0]
            return {
                'code': ts_code,
                'name': '',  # 需要从 stock_basic 获取
                'price': row.get('close', 0),
                'open': row.get('open', 0),
                'high': row.get('high', 0),
                'low': row.get('low', 0),
                'pre_close': row.get('pre_close', 0),
                'change': row.get('close', 0) - row.get('pre_close', 0),
                'change_pct': ((row.get('close', 0) - row.get('pre_close', 0)) / row.get('pre_close', 1) * 100),
                'vol': row.get('vol', 0),
                'amount': row.get('amount', 0),
                'trade_date': row.get('trade_date', ''),
            }
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return {}
    
    def get_kline(self, ts_code: str, period: str = 'daily', count: int = 100) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            ts_code: 股票代码
            period: 周期 daily/weekly/monthly
            count: 数据条数
        
        Returns:
            K线 DataFrame
        """
        if not self.pro:
            return pd.DataFrame()
        
        ts_code = self._format_code(ts_code)
        
        try:
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            if period == 'daily':
                start_date = (datetime.now() - timedelta(days=count * 2)).strftime('%Y%m%d')
            elif period == 'weekly':
                start_date = (datetime.now() - timedelta(weeks=count * 2)).strftime('%Y%m%d')
            else:  # monthly
                start_date = (datetime.now() - timedelta(days=count * 60)).strftime('%Y%m%d')
            
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return pd.DataFrame()
            
            # 只返回最近的 count 条
            return df.head(count)
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            return pd.DataFrame()

    def get_money_flow(self, ts_code: str, trade_date: str = None) -> dict:
        """
        获取个股资金流向数据
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期 YYYYMMDD，默认最新
        
        Returns:
            dict: 包含主力资金流向数据的字典
        """
        if not self.pro:
            return {}
        
        ts_code = self._format_code(ts_code)
        
        try:
            # Tushare moneyflow 接口
            if trade_date:
                df = self.pro.moneyflow(ts_code=ts_code, trade_date=trade_date)
            else:
                # 获取最近的数据
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
                df = self.pro.moneyflow(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if df is None or df.empty:
                logger.warning(f"Tushare 资金流向数据为空: {ts_code}")
                return {}
            
            # 取最新一条
            latest = df.iloc[0]
            
            # Tushare moneyflow 字段映射
            result = {
                'trade_date': latest.get('trade_date', ''),
                'buy_sm_vol': latest.get('buy_sm_vol', 0),  # 小单买入量
                'buy_sm_amount': latest.get('buy_sm_amount', 0),  # 小单买入金额
                'sell_sm_vol': latest.get('sell_sm_vol', 0),  # 小单卖出量
                'sell_sm_amount': latest.get('sell_sm_amount', 0),  # 小单卖出金额
                'buy_md_vol': latest.get('buy_md_vol', 0),  # 中单买入量
                'buy_md_amount': latest.get('buy_md_amount', 0),  # 中单买入金额
                'sell_md_vol': latest.get('sell_md_vol', 0),  # 中单卖出量
                'sell_md_amount': latest.get('sell_md_amount', 0),  # 中单卖出金额
                'buy_lg_vol': latest.get('buy_lg_vol', 0),  # 大单买入量
                'buy_lg_amount': latest.get('buy_lg_amount', 0),  # 大单买入金额
                'sell_lg_vol': latest.get('sell_lg_vol', 0),  # 大单卖出量
                'sell_lg_amount': latest.get('sell_lg_amount', 0),  # 大单卖出金额
                'buy_elg_vol': latest.get('buy_elg_vol', 0),  # 特大单买入量
                'buy_elg_amount': latest.get('buy_elg_amount', 0),  # 特大单买入金额
                'sell_elg_vol': latest.get('sell_elg_vol', 0),  # 特大单卖出量
                'sell_elg_amount': latest.get('sell_elg_amount', 0),  # 特大单卖出金额
            }
            
            # 计算净额
            result['main_net_inflow'] = (
                (result['buy_lg_amount'] + result['buy_elg_amount']) - 
                (result['sell_lg_amount'] + result['sell_elg_amount'])
            )
            result['medium_net'] = result['buy_md_amount'] - result['sell_md_amount']
            result['small_net'] = result['buy_sm_amount'] - result['sell_sm_amount']
            
            # 计算总量
            total = abs(result['main_net_inflow']) + abs(result['medium_net']) + abs(result['small_net'])
            if total > 0:
                result['main_net_inflow_pct'] = (result['main_net_inflow'] / total * 100) if total > 0 else 0
            else:
                result['main_net_inflow_pct'] = 0
            
            logger.info(f"Tushare 资金流向获取成功: {ts_code}, 主力净流入: {result['main_net_inflow']:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Tushare 获取资金流向失败: {ts_code}, {e}")
            return {}


# 全局实例（需要延迟初始化）
_tushare_client = None


def get_tushare_client() -> TushareClient:
    """获取 Tushare 客户端单例"""
    global _tushare_client
    if _tushare_client is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv('TUSHARE_TOKEN', '')
        if not token:
            raise ValueError("未配置 TUSHARE_TOKEN 环境变量")
        _tushare_client = TushareClient(token)
    return _tushare_client
