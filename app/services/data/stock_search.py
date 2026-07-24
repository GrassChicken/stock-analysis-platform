"""
股票搜索服务 - 基于 AKShare

支持代码、名称搜索
"""
import logging
from typing import List, Dict, Any
import akshare as ak

logger = logging.getLogger(__name__)


class StockSearchService:
    """股票搜索服务"""
    
    def __init__(self):
        self._stock_list_cache = None
    
    def _get_all_stocks(self) -> List[Dict[str, Any]]:
        """获取所有 A 股股票列表（带内存缓存）"""
        if self._stock_list_cache:
            return self._stock_list_cache
        
        try:
            # 使用 stock_info_a_code_name 接口 - 稳定可靠
            df = ak.stock_info_a_code_name()
            if df is None or df.empty:
                logger.warning("AKShare 返回空数据")
                return []
            
            stock_list = []
            for _, row in df.iterrows():
                code = str(row.get('code', '')).strip()
                name = str(row.get('name', '')).strip()
                
                # 只保留 A 股股票（排除指数、基金、债券等）
                if code.startswith(('000', '001', '002', '003', '300', '600', '601', '603', '688')):
                    stock_list.append({
                        'code': code,
                        'name': name,
                        'market': 'SH' if code.startswith('6') else 'SZ',
                    })
            
            self._stock_list_cache = stock_list
            logger.info(f"✓ 已加载 {len(stock_list)} 只股票到搜索索引")
            return stock_list
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def search(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词（代码/名称）
            limit: 返回数量限制
        
        Returns:
            匹配的股票列表
        """
        if not keyword:
            return []
        
        keyword = keyword.strip()
        stocks = self._get_all_stocks()
        
        results = []
        
        for stock in stocks:
            code = stock['code']
            name = stock['name']
            
            # 代码匹配（支持部分匹配）
            if keyword.isdigit() and keyword in code:
                results.append({
                    'code': code,
                    'name': name,
                    'market': stock['market'],
                    'match_type': 'code'
                })
                if len(results) >= limit:
                    break
            
            # 名称匹配（支持中文部分匹配）
            elif not keyword.isdigit() and keyword in name:
                results.append({
                    'code': code,
                    'name': name,
                    'market': stock['market'],
                    'match_type': 'name'
                })
                if len(results) >= limit:
                    break
        
        return results
    
    def search_by_code(self, code: str) -> Dict[str, Any] | None:
        """根据代码精确搜索"""
        stocks = self._get_all_stocks()
        for stock in stocks:
            if stock['code'] == code:
                return {
                    'code': stock['code'],
                    'name': stock['name'],
                    'market': stock['market'],
                }
        return None


# 全局实例
stock_search = StockSearchService()
