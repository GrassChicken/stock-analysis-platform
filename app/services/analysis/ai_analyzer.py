"""
AI 分析引擎

使用大模型生成股票深度分析报告
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from openai import OpenAI


class AIAnalyzer:
    """AI 分析引擎"""
    
    def __init__(self):
        """初始化 AI 客户端"""
        api_key = os.getenv('AI_API_KEY')
        base_url = os.getenv('AI_API_BASE', 'https://api.openai.com/v1')
        
        if not api_key:
            raise ValueError("AI_API_KEY 未配置")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = os.getenv('AI_MODEL', 'qwen-plus')
        self._cache = {}  # 简单的内存缓存
        self._cache_timestamps = {}  # 缓存时间戳
        self._cache_ttl = timedelta(hours=24)  # 缓存有效期 24 小时
    
    def _get_cache_key(self, stock_data: Dict[str, Any]) -> str:
        """生成缓存键"""
        return f"ai_analysis_{stock_data.get('code', 'unknown')}_{datetime.now().strftime('%Y%m%d')}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存结果"""
        if cache_key in self._cache:
            cached_time = self._cache_timestamps.get(cache_key)
            if cached_time and datetime.now() - cached_time < self._cache_ttl:
                return self._cache[cache_key]
        return None
    
    def _set_cache_result(self, cache_key: str, result: Dict[str, Any]):
        """设置缓存结果"""
        self._cache[cache_key] = result
        self._cache_timestamps[cache_key] = datetime.now()
    
    def analyze(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成股票深度分析报告
        
        Args:
            stock_data: 股票综合数据（包含六维评分）
        
        Returns:
            AI 分析报告
        """
        # 构建分析提示词
        prompt = self._build_prompt(stock_data)
        
        try:
            # 调用 AI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的股票分析师，擅长基本面、技术面、资金面等多维度分析。请基于提供的数据给出专业、客观的投资建议。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            analysis_text = response.choices[0].message.content
            
            return {
                'success': True,
                'analysis': analysis_text,
                'model': self.model
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'analysis': None
            }
    
    def _build_prompt(self, stock_data: Dict[str, Any]) -> str:
        """
        构建 AI 分析提示词
        
        Args:
            stock_data: 股票数据
        
        Returns:
            提示词文本
        """
        stock_info = stock_data.get('stock_info', {})
        score_data = stock_data.get('score_data', {})
        fundamental = stock_data.get('fundamental', {})
        technical = stock_data.get('technical', {})
        valuation = stock_data.get('valuation', {})
        capital = stock_data.get('capital', {})
        industry = stock_data.get('industry', {})
        
        prompt = f"""请对以下股票进行深度分析，生成一份专业的投资分析报告。

## 基本信息
- 股票代码：{stock_info.get('code', 'N/A')}
- 股票名称：{stock_info.get('name', 'N/A')}
- 所属行业：{stock_info.get('industry', 'N/A')}

## 综合评分
- 总分：{score_data.get('total_score', 0)}/100
- 评级：{score_data.get('rating', 'N/A')}
- 基本面评分：{score_data.get('fundamental_score', 0)}/100
- 估值面评分：{score_data.get('valuation_score', 0)}/100
- 成长性评分：{score_data.get('growth_score', 0)}/100
- 技术面评分：{score_data.get('technical_score', 0)}/100
- 资金面评分：{score_data.get('capital_score', 0)}/100
- 行业面评分：{score_data.get('industry_score', 0)}/100

## 基本面数据
- ROE：{fundamental.get('roe', 'N/A')}%
- 净利率：{fundamental.get('net_margin', 'N/A')}%
- 资产负债率：{fundamental.get('debt_ratio', 'N/A')}%
- 营收同比增长：{fundamental.get('revenue_yoy', 'N/A')}%
- 净利润同比增长：{fundamental.get('profit_yoy', 'N/A')}%

## 技术面数据
- 当前价格：{technical.get('current_price', 'N/A')}
- 均线排列：{technical.get('ma_arrangement', 'N/A')}
- MACD状态：{technical.get('macd_status', 'N/A')}
- KDJ状态：{technical.get('kdj_status', 'N/A')}
- 支撑位：{technical.get('support_levels', 'N/A')}
- 阻力位：{technical.get('resistance_levels', 'N/A')}

## 估值面数据
- PE（TTM）：{valuation.get('pe_ttm', 'N/A')}
- PB：{valuation.get('pb', 'N/A')}
- PS：{valuation.get('ps', 'N/A')}
- PE历史分位：{valuation.get('pe_percentile', 'N/A')}%
- PB历史分位：{valuation.get('pb_percentile', 'N/A')}%

## 资金面数据
- 主力资金流向：{capital.get('main_flow', 'N/A')}
- 北向资金持股：{capital.get('north_hold', 'N/A')}
- 融资余额变化：{capital.get('margin_change', 'N/A')}

## 行业面数据
- 行业热度：{industry.get('heat', 'N/A')}
- 行业排名：{industry.get('rank', 'N/A')}
- 行业趋势：{industry.get('trend', 'N/A')}

请从以下维度进行分析：

1. **核心优势**（3-5点）
2. **主要风险**（3-5点）
3. **投资建议**（短期/中期/长期）
4. **操作建议**（买入价位、目标价位、止损价位）

请用专业、客观的语言，给出有理有据的分析。
"""
        
        return prompt


# 单例模式
_ai_analyzer = None


def get_ai_analyzer() -> AIAnalyzer:
    """获取 AI 分析器实例"""
    global _ai_analyzer
    if _ai_analyzer is None:
        _ai_analyzer = AIAnalyzer()
    return _ai_analyzer
