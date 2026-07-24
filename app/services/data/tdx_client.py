"""
通达信 pytdx 客户端封装

提供统一的接口访问通达信服务器数据
"""
import logging
from typing import List, Dict, Any, Optional
from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API

logger = logging.getLogger(__name__)


class TdxClient:
    """通达信客户端"""
    
    # 常用通达信服务器列表
    DEFAULT_SERVERS = [
        ("119.147.212.81", 7709),
        ("114.80.63.12", 7709),
        ("218.75.126.9", 7709),
        ("221.194.181.176", 7709),
        ("59.175.238.38", 7709),
    ]
    
    def __init__(self):
        self.api = None
        self.connected = False
        self.current_server = None
    
    def connect(self, server_ip: str = None, server_port: int = 7709) -> bool:
        """连接通达信服务器"""
        if self.connected:
            return True
        
        try:
            self.api = TdxHq_API()
            
            # 如果没指定服务器，自动选择最优
            if server_ip:
                self.api.connect(server_ip, server_port)
                self.current_server = (server_ip, server_port)
            else:
                # 尝试连接默认服务器列表
                for ip, port in self.DEFAULT_SERVERS:
                    try:
                        self.api.connect(ip, port)
                        self.current_server = (ip, port)
                        logger.info(f"✅ 连接通达信成功: {ip}:{port}")
                        break
                    except Exception as e:
                        logger.debug(f"连接 {ip}:{port} 失败: {e}")
                        continue
            
            if self.current_server:
                self.connected = True
                return True
            else:
                logger.error("❌ 所有通达信服务器连接失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 连接通达信异常: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.api and self.connected:
            try:
                self.api.disconnect()
            except Exception as e:
                logger.error(f"断开连接异常: {e}")
            finally:
                self.connected = False
                self.current_server = None
    
    def _ensure_connected(self):
        """确保已连接"""
        if not self.connected:
            if not self.connect():
                raise Exception("无法连接通达信服务器")
    
    def get_security_quotes(self, stock_list: List[tuple]) -> List[Dict[str, Any]]:
        """
        获取实时行情
        
        Args:
            stock_list: [(market, code), ...] market: 0=深圳 1=上海
        
        Returns:
            行情数据列表
        """
        self._ensure_connected()
        
        try:
            data = self.api.get_security_quotes(stock_list)
            if data is None:
                return []
            
            result = []
            for item in data:
                result.append({
                    'code': item.get('code', ''),
                    'market': item.get('market', 0),
                    'price': item.get('price', 0),
                    'last_close': item.get('last_close', 0),
                    'open': item.get('open', 0),
                    'high': item.get('high', 0),
                    'low': item.get('low', 0),
                    'vol': item.get('vol', 0),
                    'cur_vol': item.get('cur_vol', 0),
                    'amount': item.get('amount', 0),
                    's_vol': item.get('s_vol', 0),
                    'b_vol': item.get('b_vol', 0),
                    'bid1': item.get('bid1', 0),
                    'ask1': item.get('ask1', 0),
                    'bid_vol1': item.get('bid_vol1', 0),
                    'ask_vol1': item.get('ask_vol1', 0),
                })
            return result
            
        except Exception as e:
            logger.error(f"获取行情失败: {e}")
            return []
    
    def get_security_bars(self, category: int, market: int, code: str, start: int, count: int) -> List[Dict[str, Any]]:
        """
        获取K线数据
        
        Args:
            category: K线类型 0=5分钟 1=15分钟 2=30分钟 3=1小时 4=日线 5=周线 6=月线 7=1分钟 8=年线 9=季线 10=120分钟
            market: 市场 0=深圳 1=上海
            code: 股票代码
            start: 起始位置 (0=最新)
            count: 数量
        
        Returns:
            K线数据列表
        """
        self._ensure_connected()
        
        try:
            data = self.api.get_security_bars(category, market, code, start, count)
            if data is None:
                return []
            
            result = []
            for item in data:
                result.append({
                    'open': item.get('open', 0),
                    'high': item.get('high', 0),
                    'low': item.get('low', 0),
                    'close': item.get('close', 0),
                    'vol': item.get('vol', 0),
                    'amount': item.get('amount', 0),
                    'datetime': item.get('datetime', ''),
                })
            return result
            
        except Exception as e:
            logger.error(f"获取K线失败: {e}")
            return []
    
    def get_security_count(self, market: int) -> int:
        """获取市场股票数量"""
        self._ensure_connected()
        try:
            return self.api.get_security_count(market)
        except Exception as e:
            logger.error(f"获取股票数量失败: {e}")
            return 0
    
    def get_security_list(self, market: int, start: int = 0) -> List[Dict[str, Any]]:
        """
        获取股票列表
        
        Args:
            market: 市场 0=深圳 1=上海
            start: 起始位置
        
        Returns:
            股票列表
        """
        self._ensure_connected()
        
        try:
            data = self.api.get_security_list(market, start)
            if data is None:
                return []
            
            result = []
            for item in data:
                result.append({
                    'code': item.get('code', ''),
                    'volunit': item.get('volunit', 0),
                    'decimal_point': item.get('decimal_point', 2),
                    'name': item.get('name', ''),
                    'pre_close': item.get('pre_close', 0),
                })
            return result
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_finance_info(self, market: int, code: str) -> Dict[str, Any]:
        """
        获取财务数据
        
        Args:
            market: 市场 0=深圳 1=上海
            code: 股票代码
        
        Returns:
            财务数据字典
        """
        self._ensure_connected()
        
        try:
            data = self.api.get_finance_info(market, code)
            if data is None:
                return {}
            
            return {
                'total_share': data.get('totalShare', 0),  # 总股本
                'float_share': data.get('floatShare', 0),  # 流通股本
                'total_asset': data.get('totalAsset', 0),  # 总资产
                'liquid_asset': data.get('liquidAsset', 0),  # 流动资产
                'fixed_asset': data.get('fixedAsset', 0),  # 固定资产
                'reserved': data.get('reserved', 0),  # 公积金
                'reserved_per_share': data.get('reservedPerShare', 0),  # 每股公积金
                'eps': data.get('earning_per_share', 0),  # 每股收益
                'net_profit': data.get('netProfit', 0),  # 净利润
                'turnover': data.get('turnover', 0),  # 营业收入
                'profit_four_quarter': data.get('profit_four_quarter', 0),  # 四季度净利润
            }
            
        except Exception as e:
            logger.error(f"获取财务数据失败: {e}")
            return {}
    
    def get_company_info(self, market: int, code: str) -> Dict[str, Any]:
        """
        获取公司信息
        
        Args:
            market: 市场 0=深圳 1=上海
            code: 股票代码
        
        Returns:
            公司信息字典
        """
        self._ensure_connected()
        
        try:
            # 公司概况
            data = self.api.get_company_info(market, code)
            if data is None:
                return {}
            
            return {
                'name': data.get('name', ''),
                'english_name': data.get('ename', ''),
                'market': data.get('market', ''),
                'idea': data.get('idea', ''),  # 概念
                'listed_date': data.get('l_date', ''),  # 上市日期
                'stock_code': data.get('stockcode', ''),
                'issue_price': data.get('price', 0),  # 发行价
                'principal': data.get('principal', ''),  # 主承销商
                'listing_volume': data.get('volume', 0),  # 上市总量
                'fee_ratio': data.get('fee_ratio', 0),  # 手续费率
                'accounting_firm': data.get('account', ''),  # 会计师事务所
                'eps': data.get('earnings', 0),  # 每股收益
                'net_asset_per_share': data.get('issue_pe', 0),  # 每股净资产
                'last_four_quarter_profit': data.get('profit', 0),  # 四季度净利润
            }
            
        except Exception as e:
            logger.error(f"获取公司信息失败: {e}")
            return {}
    
    def get_xdxr_data(self, market: int, code: str) -> List[Dict[str, Any]]:
        """
        获取除权除息数据
        
        Args:
            market: 市场 0=深圳 1=上海
            code: 股票代码
        
        Returns:
            除权除息数据列表
        """
        self._ensure_connected()
        
        try:
            data = self.api.get_xdxr_data(market, code)
            if data is None:
                return []
            
            result = []
            for item in data:
                result.append({
                    'datetime': item.get('datetime', ''),
                    'category': item.get('category', 0),  # 1=除权 2=除息 3=配股 4=转增
                    'price': item.get('price', 0),
                    'vol': item.get('vol', 0),
                    'amount': item.get('amount', 0),
                    'fenhong': item.get('fenhong', 0),  # 分红
                    'peigu': item.get('peigu', 0),  # 配股
                    'peigujia': item.get('peigujia', 0),  # 配股价
                    'songzhuangu': item.get('songzhuangu', 0),  # 送转股
                })
            return result
            
        except Exception as e:
            logger.error(f"获取除权除息数据失败: {e}")
            return []
    
    def get_block_info(self, block_type: str = "industry") -> List[Dict[str, Any]]:
        """
        获取板块信息
        
        Args:
            block_type: 板块类型 "industry"=行业 "concept"=概念 "area"=地域
        
        Returns:
            板块列表
        """
        self._ensure_connected()
        
        try:
            # pytdx 板块类型映射
            type_map = {
                'industry': 'tdxhy.cfg',
                'concept': 'tdxgn.cfg',
                'area': 'tdxzs.cfg'
            }
            
            block_file = type_map.get(block_type, 'tdxhy.cfg')
            data = self.api.get_and_parse_block_file(block_file)
            
            if data is None:
                return []
            
            result = []
            for item in data:
                result.append({
                    'block_name': item.get('block_name', ''),
                    'stock_list': item.get('stock_list', []),
                    'stock_list_len': item.get('stock_list_len', 0),
                })
            return result
            
        except Exception as e:
            logger.error(f"获取板块信息失败: {e}")
            return []
    
    def get_index_bars(self, category: int, market: int, code: str, start: int, count: int) -> List[Dict[str, Any]]:
        """
        获取指数K线
        
        Args:
            category: K线类型 (同 get_security_bars)
            market: 市场
            code: 指数代码 (如 000001 上证指数)
            start: 起始位置
            count: 数量
        
        Returns:
            K线数据列表
        """
        self._ensure_connected()
        
        try:
            data = self.api.get_index_bars(category, market, code, start, count)
            if data is None:
                return []
            
            result = []
            for item in data:
                result.append({
                    'open': item.get('open', 0),
                    'high': item.get('high', 0),
                    'low': item.get('low', 0),
                    'close': item.get('close', 0),
                    'vol': item.get('vol', 0),
                    'amount': item.get('amount', 0),
                    'datetime': item.get('datetime', ''),
                })
            return result
            
        except Exception as e:
            logger.error(f"获取指数K线失败: {e}")
            return []
