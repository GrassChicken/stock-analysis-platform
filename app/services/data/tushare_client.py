"""
Tushare 数据客户端

提供稳定的 A 股数据获取能力
"""
import logging
from typing import List, Dict, Any, Optional
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


# 全局实例（需要延迟初始化）
_tushare_client = None


def get_tushare_client() -> TushareClient:
    """获取 Tushare 客户端单例"""
    global _tushare_client
    if _tushare_client is None:
        import os
        token = os.getenv('TUSHARE_TOKEN', '')
        if not token:
            raise ValueError("未配置 TUSHARE_TOKEN 环境变量")
        _tushare_client = TushareClient(token)
    return _tushare_client
