"""
财务数据服务

提供财务报表和财务指标数据
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import pandas as pd

from app.services.data.tushare_client import get_tushare_client
from app.services.data.cache_manager import cached, cache_get, cache_set, CACHE_TTL

logger = logging.getLogger(__name__)


class FinanceService:
    """财务数据服务"""

    def _get_pro(self):
        """获取 Tushare pro 接口"""
        client = get_tushare_client()
        return client.pro

    def _format_code(self, code: str) -> str:
        """格式化股票代码"""
        code = code.strip().upper()
        if '.' in code:
            return code
        if code.startswith(('6', '9')):
            return f"{code}.SH"
        else:
            return f"{code}.SZ"

    def get_financial_statements(self, code: str) -> Dict[str, Any]:
        """
        获取三大财务报表（利润表 + 资产负债表 + 现金流）
        
        Args:
            code: 股票代码
        
        Returns:
            包含三大报表的字典
        """
        ts_code = self._format_code(code)
        
        # 检查缓存
        cache_key = f"financial_statements:{ts_code}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        pro = self._get_pro()
        if not pro:
            return {}

        try:
            # 获取利润表
            income_df = pro.income(
                ts_code=ts_code,
                fields='ts_code,ann_date,f_ann_date,end_date,report_type,comp_type,basic_eps,diluted_eps,total_revenue,revenue,total_cogs,oper_cost,operate_profit,total_profit,n_income,n_income_attr_p'
            )
            time.sleep(0.3)
            
            # 获取资产负债表
            balance_df = pro.balancesheet(
                ts_code=ts_code,
                fields='ts_code,end_date,report_type,total_assets,total_liab,total_hldr_eqy_exc_min_int,total_hldr_eqy_inc_min_int'
            )
            time.sleep(0.3)
            
            # 获取现金流表
            cashflow_df = pro.cashflow(
                ts_code=ts_code,
                fields='ts_code,end_date,report_type,n_cashflow_act,n_cashflow_inv_act,n_cash_flows_fnc_act'
            )
            time.sleep(0.3)
            
            result = {
                'ts_code': ts_code,
                'income': self._df_to_list(income_df) if not income_df.empty else [],
                'balance': self._df_to_list(balance_df) if not balance_df.empty else [],
                'cashflow': self._df_to_list(cashflow_df) if not cashflow_df.empty else [],
            }
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['finance'])
            
            return result
        except Exception as e:
            logger.error(f"获取财务报表失败 {ts_code}: {e}")
            return {}

    def get_fina_indicators(self, code: str) -> Dict[str, Any]:
        """
        获取财务指标（ROE/毛利率/净利率/负债率等）
        
        Args:
            code: 股票代码
        
        Returns:
            财务指标字典
        """
        ts_code = self._format_code(code)
        
        # 检查缓存
        cache_key = f"fina_indicators:{ts_code}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        pro = self._get_pro()
        if not pro:
            return {}

        try:
            df = pro.fina_indicator(
                ts_code=ts_code,
                fields='ts_code,end_date,eps,dt_eps,bps,roe,roe_waa,roe_dt,grossprofit_margin,netprofit_margin,op_yoy,dt_netprofit_yoy,tr_yoy,or_yoy,current_ratio,quick_ratio,debt_to_assets,assets_turn,fix_ass_ratio'
            )
            time.sleep(0.3)
            
            if df.empty:
                return {}
            
            # 获取最近一期
            row = df.iloc[0]
            
            result = {
                'ts_code': ts_code,
                'end_date': str(row.get('end_date', '')),
                'eps': self._safe_float(row.get('eps')),
                'dt_eps': self._safe_float(row.get('dt_eps')),
                'bps': self._safe_float(row.get('bps')),
                'roe': self._safe_float(row.get('roe')),
                'roe_waa': self._safe_float(row.get('roe_waa')),
                'roe_dt': self._safe_float(row.get('roe_dt')),
                'grossprofit_margin': self._safe_float(row.get('grossprofit_margin')),
                'netprofit_margin': self._safe_float(row.get('netprofit_margin')),
                'op_yoy': self._safe_float(row.get('op_yoy')),
                'dt_netprofit_yoy': self._safe_float(row.get('dt_netprofit_yoy')),
                'tr_yoy': self._safe_float(row.get('tr_yoy')),
                'or_yoy': self._safe_float(row.get('or_yoy')),
                'current_ratio': self._safe_float(row.get('current_ratio')),
                'quick_ratio': self._safe_float(row.get('quick_ratio')),
                'debt_to_assets': self._safe_float(row.get('debt_to_assets')),
                'assets_turn': self._safe_float(row.get('assets_turn')),
                'fix_ass_ratio': self._safe_float(row.get('fix_ass_ratio')),
            }
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['finance'])
            
            return result
        except Exception as e:
            logger.error(f"获取财务指标失败 {ts_code}: {e}")
            return {}

    def get_fina_indicators_history(self, code: str, quarters: int = 8) -> List[Dict[str, Any]]:
        """
        获取近 N 季度财务指标趋势
        
        Args:
            code: 股票代码
            quarters: 季度数，默认 8
        
        Returns:
            财务指标历史数据列表
        """
        ts_code = self._format_code(code)
        
        # 检查缓存
        cache_key = f"fina_indicators_history:{ts_code}:{quarters}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        pro = self._get_pro()
        if not pro:
            return []

        try:
            df = pro.fina_indicator(
                ts_code=ts_code,
                fields='ts_code,end_date,eps,dt_eps,bps,roe,roe_waa,roe_dt,grossprofit_margin,netprofit_margin,op_yoy,dt_netprofit_yoy,tr_yoy,or_yoy,current_ratio,quick_ratio,debt_to_assets,assets_turn,fix_ass_ratio'
            )
            time.sleep(0.3)
            
            if df.empty:
                return []
            
            # 去重：按 end_date 去重（保留第一条）
            if 'end_date' in df.columns:
                df = df.drop_duplicates(subset=['end_date'], keep='first')
            # 只取最近的 N 条
            df = df.head(quarters)
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    'end_date': str(row.get('end_date', '')),
                    'eps': self._safe_float(row.get('eps')),
                    'dt_eps': self._safe_float(row.get('dt_eps')),
                    'bps': self._safe_float(row.get('bps')),
                    'roe': self._safe_float(row.get('roe')),
                    'roe_waa': self._safe_float(row.get('roe_waa')),
                    'roe_dt': self._safe_float(row.get('roe_dt')),
                    'grossprofit_margin': self._safe_float(row.get('grossprofit_margin')),
                    'netprofit_margin': self._safe_float(row.get('netprofit_margin')),
                    'op_yoy': self._safe_float(row.get('op_yoy')),
                    'dt_netprofit_yoy': self._safe_float(row.get('dt_netprofit_yoy')),
                    'tr_yoy': self._safe_float(row.get('tr_yoy')),
                    'or_yoy': self._safe_float(row.get('or_yoy')),
                    'current_ratio': self._safe_float(row.get('current_ratio')),
                    'quick_ratio': self._safe_float(row.get('quick_ratio')),
                    'debt_to_assets': self._safe_float(row.get('debt_to_assets')),
                    'assets_turn': self._safe_float(row.get('assets_turn')),
                    'fix_ass_ratio': self._safe_float(row.get('fix_ass_ratio')),
                })
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['finance'])
            
            return result
        except Exception as e:
            logger.error(f"获取财务指标历史失败 {ts_code}: {e}")
            return []

    def get_income_history(self, code: str, quarters: int = 8) -> List[Dict[str, Any]]:
        """
        获取近 N 季度利润表趋势
        
        Args:
            code: 股票代码
            quarters: 季度数，默认 8
        
        Returns:
            利润表历史数据列表
        """
        ts_code = self._format_code(code)
        
        # 检查缓存
        cache_key = f"income_history:{ts_code}:{quarters}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        pro = self._get_pro()
        if not pro:
            return []

        try:
            df = pro.income(
                ts_code=ts_code,
                fields='ts_code,ann_date,end_date,report_type,basic_eps,total_revenue,revenue,oper_cost,operate_profit,total_profit,n_income,n_income_attr_p'
            )
            time.sleep(0.3)
            
            if df.empty:
                return []
            
            # 去重：按 end_date 去重（保留第一条）
            if 'end_date' in df.columns:
                df = df.drop_duplicates(subset=['end_date'], keep='first')
            # 只取最近的 N 条
            df = df.head(quarters)
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    'end_date': str(row.get('end_date', '')),
                    'report_type': str(row.get('report_type', '')),
                    'basic_eps': self._safe_float(row.get('basic_eps')),
                    'total_revenue': self._safe_float(row.get('total_revenue')),
                    'revenue': self._safe_float(row.get('revenue')),
                    'oper_cost': self._safe_float(row.get('oper_cost')),
                    'operate_profit': self._safe_float(row.get('operate_profit')),
                    'total_profit': self._safe_float(row.get('total_profit')),
                    'n_income': self._safe_float(row.get('n_income')),
                    'n_income_attr_p': self._safe_float(row.get('n_income_attr_p')),
                })
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['finance'])
            
            return result
        except Exception as e:
            logger.error(f"获取利润表历史失败 {ts_code}: {e}")
            return []

    def get_balance_history(self, code: str, quarters: int = 8) -> List[Dict[str, Any]]:
        """
        获取近 N 季度资产负债表趋势
        
        Args:
            code: 股票代码
            quarters: 季度数，默认 8
        
        Returns:
            资产负债表历史数据列表
        """
        ts_code = self._format_code(code)
        
        # 检查缓存
        cache_key = f"balance_history:{ts_code}:{quarters}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        pro = self._get_pro()
        if not pro:
            return []

        try:
            df = pro.balancesheet(
                ts_code=ts_code,
                fields='ts_code,end_date,report_type,total_assets,total_liab,total_hldr_eqy_exc_min_int,total_hldr_eqy_inc_min_int'
            )
            time.sleep(0.3)
            
            if df.empty:
                return []
            
            # 去重：按 end_date 去重（保留第一条）
            if 'end_date' in df.columns:
                df = df.drop_duplicates(subset=['end_date'], keep='first')
            # 只取最近的 N 条
            df = df.head(quarters)
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    'end_date': str(row.get('end_date', '')),
                    'report_type': str(row.get('report_type', '')),
                    'total_assets': self._safe_float(row.get('total_assets')),
                    'total_liab': self._safe_float(row.get('total_liab')),
                    'total_hldr_eqy_exc_min_int': self._safe_float(row.get('total_hldr_eqy_exc_min_int')),
                    'total_hldr_eqy_inc_min_int': self._safe_float(row.get('total_hldr_eqy_inc_min_int')),
                })
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['finance'])
            
            return result
        except Exception as e:
            logger.error(f"获取资产负债表历史失败 {ts_code}: {e}")
            return []

    def get_cashflow_history(self, code: str, quarters: int = 8) -> List[Dict[str, Any]]:
        """
        获取近 N 季度现金流量表趋势
        
        Args:
            code: 股票代码
            quarters: 季度数，默认 8
        
        Returns:
            现金流量表历史数据列表
        """
        ts_code = self._format_code(code)
        
        # 检查缓存
        cache_key = f"cashflow_history:{ts_code}:{quarters}"
        cached_result = cache_get(cache_key)
        if cached_result is not None:
            return cached_result

        pro = self._get_pro()
        if not pro:
            return []

        try:
            df = pro.cashflow(
                ts_code=ts_code,
                fields='ts_code,end_date,report_type,n_cashflow_act,n_cashflow_inv_act,n_cash_flows_fnc_act'
            )
            time.sleep(0.3)
            
            if df.empty:
                return []
            
            # 去重：按 end_date 去重（保留第一条）
            if 'end_date' in df.columns:
                df = df.drop_duplicates(subset=['end_date'], keep='first')
            # 只取最近的 N 条
            df = df.head(quarters)
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    'end_date': str(row.get('end_date', '')),
                    'report_type': str(row.get('report_type', '')),
                    'n_cashflow_act': self._safe_float(row.get('n_cashflow_act')),
                    'n_cashflow_inv_act': self._safe_float(row.get('n_cashflow_inv_act')),
                    'n_cash_flows_fnc_act': self._safe_float(row.get('n_cash_flows_fnc_act')),
                })
            
            # 写入缓存
            cache_set(cache_key, result, timeout=CACHE_TTL['finance'])
            
            return result
        except Exception as e:
            logger.error(f"获取现金流量表历史失败 {ts_code}: {e}")
            return []

    def _safe_float(self, value) -> float:
        """安全转换为 float，None 或无效值返回 0.0"""
        if value is None or pd.isna(value):
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    def _df_to_list(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """将 DataFrame 转为 dict 列表，数值安全转换"""
        result = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                val = row[col]
                if isinstance(val, (int, float)) and not pd.isna(val):
                    record[col] = float(val)
                elif pd.isna(val):
                    record[col] = 0.0 if isinstance(val, (int, float)) else ''
                else:
                    record[col] = str(val)
            result.append(record)
        return result


# 全局单例
finance_service = FinanceService()
