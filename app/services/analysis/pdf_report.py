"""
PDF 报告生成服务

使用 fpdf2 生成 PDF 分析报告，支持中文
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any
from fpdf import FPDF

logger = logging.getLogger(__name__)

# 字体路径
FONT_DIR = '/usr/share/fonts'
CN_FONT_PATH = os.path.join(FONT_DIR, 'NotoSansSC-Regular.ttf')


class StockReportPDF:
    """股票分析报告 PDF 生成器"""
    
    def __init__(self):
        self.pdf = FPDF()
        self._load_font()
    
    def _load_font(self):
        """加载中文字体"""
        if os.path.exists(CN_FONT_PATH):
            self.pdf.add_font('NotoSansSC', '', CN_FONT_PATH, uni=True)
            self.pdf.add_font('NotoSansSC', 'B', CN_FONT_PATH, uni=True)
        else:
            logger.warning(f"中文字体不存在: {CN_FONT_PATH}, 将使用默认字体")
    
    def _set_cn_font(self, style='', size=12):
        """设置中文字体"""
        font_name = 'NotoSansSC' if os.path.exists(CN_FONT_PATH) else 'Helvetica'
        self.pdf.set_font(font_name, style, size)
    
    def _safe_text(self, text: str) -> str:
        """清理文本中的特殊字符"""
        if text is None:
            return ''
        return str(text).replace('\r', '').replace('\x00', '')
    
    def _safe_fmt(self, value, fmt_str='.2f', default='--'):
        """安全格式化数值，处理 None 情况"""
        if value is None:
            return default
        try:
            return format(float(value), fmt_str)
        except:
            return default
    
    def generate(self, data: Dict[str, Any]) -> str:
        """
        生成 PDF 报告
        
        Args:
            data: 股票数据字典（来自 scorer + valuation + fundamental + technical）
        
        Returns:
            PDF 文件路径
        """
        code = data.get('code', '')
        name = data.get('name', code)
        
        self.pdf.add_page()
        self._render_header(name, code, data)
        self._render_score(data)
        self._render_fundamental(data)
        self._render_valuation(data)
        self._render_technical(data)
        self._render_footer()
        
        # 保存文件
        output_dir = '/root/.openclaw/workspace-fafaxia/projects/stock-analysis-platform/reports'
        os.makedirs(output_dir, exist_ok=True)
        filename = f"report_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(output_dir, filename)
        self.pdf.output(filepath)
        
        logger.info(f"✓ PDF 报告已生成: {filepath}")
        return filepath
    
    def _render_header(self, name, code, data):
        """渲染报告头部"""
        self._set_cn_font('B', 22)
        self.pdf.set_text_color(30, 58, 95)
        self.pdf.cell(0, 15, self._safe_text(f'{name} ({code})'), ln=True, align='C')
        
        self._set_cn_font('', 10)
        self.pdf.set_text_color(100, 100, 100)
        self.pdf.cell(0, 8, f'分析报告 | {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
        
        # 分隔线
        self.pdf.ln(5)
        self.pdf.set_draw_color(59, 130, 246)
        self.pdf.set_line_width(0.5)
        self.pdf.line(20, self.pdf.get_y(), 190, self.pdf.get_y())
        self.pdf.ln(8)
    
    def _section_title(self, title: str):
        """渲染章节标题"""
        self.pdf.ln(4)
        self._set_cn_font('B', 14)
        self.pdf.set_text_color(30, 58, 95)
        self.pdf.cell(0, 10, self._safe_text(title), ln=True)
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.set_line_width(0.3)
        self.pdf.line(20, self.pdf.get_y(), 190, self.pdf.get_y())
        self.pdf.ln(3)
    
    def _row(self, label: str, value: str, value_color=None):
        """渲染一行数据"""
        self._set_cn_font('', 10)
        self.pdf.set_text_color(120, 120, 120)
        self.pdf.cell(70, 7, self._safe_text(label))
        
        self._set_cn_font('B', 10)
        if value_color == 'red':
            self.pdf.set_text_color(239, 68, 68)
        elif value_color == 'green':
            self.pdf.set_text_color(34, 197, 94)
        else:
            self.pdf.set_text_color(50, 50, 50)
        
        self.pdf.cell(0, 7, self._safe_text(value), ln=True)
    
    def _render_score(self, data):
        """渲染综合评分"""
        score_data = data.get('score', {})
        if not score_data:
            return
        
        self._section_title('📊 综合评分')
        
        total = score_data.get('total_score', 0) or 0
        rating = score_data.get('rating', '--') or '--'
        
        self._set_cn_font('B', 20)
        if total >= 70:
            self.pdf.set_text_color(34, 197, 94)
        elif total >= 50:
            self.pdf.set_text_color(59, 130, 246)
        elif total >= 30:
            self.pdf.set_text_color(245, 158, 11)
        else:
            self.pdf.set_text_color(239, 68, 68)
        
        self.pdf.cell(90, 12, f'{total:.1f} 分', align='L')
        self.pdf.cell(0, 12, f'评级: {rating}', ln=True, align='L')
        self.pdf.ln(3)
        
        # 六维度明细
        breakdown = score_data.get('breakdown', {})
        dim_names = {
            'fundamental_score': '基本面',
            'technical_score': '技术面',
            'valuation_score': '估值面',
            'capital_score': '资金面',
            'industry_score': '行业面',
            'growth_score': '成长性'
        }
        
        for key, label in dim_names.items():
            val = breakdown.get(key, 0)
            if isinstance(val, (int, float)):
                self._row(label, f'{val:.1f} 分')
            else:
                self._row(label, '--')
    
    def _render_fundamental(self, data):
        """渲染基本面分析"""
        fundamental = data.get('fundamental', {})
        if not fundamental:
            return
        
        self._section_title(' 基本面分析')
        
        profitability = fundamental.get('profitability', {}) or {}
        growth = fundamental.get('growth', {}) or {}
        solvency = fundamental.get('solvency', {}) or {}
        cashflow = fundamental.get('cashflow', {}) or {}
        
        self.pdf.ln(2)
        self._set_cn_font('B', 11)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.cell(0, 7, '盈利能力', ln=True)
        
        self._row('ROE', f"{self._safe_fmt(profitability.get('roe'))}%")
        self._row('净利率', f"{self._safe_fmt(profitability.get('net_margin'))}%")
        self._row('毛利率', f"{self._safe_fmt(profitability.get('gross_margin'))}%")
        self._row('EPS', f"{self._safe_fmt(profitability.get('eps'))} 元")
        
        self.pdf.ln(3)
        self._set_cn_font('B', 11)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.cell(0, 7, '成长性', ln=True)
        
        rev_yoy = growth.get('revenue_yoy')
        profit_yoy = growth.get('profit_yoy')
        self._row('营收同比', f"{self._safe_fmt(rev_yoy)}%", 'green' if rev_yoy and rev_yoy > 0 else 'red')
        self._row('利润同比', f"{self._safe_fmt(profit_yoy)}%", 'green' if profit_yoy and profit_yoy > 0 else 'red')
        
        self.pdf.ln(3)
        self._set_cn_font('B', 11)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.cell(0, 7, '偿债能力', ln=True)
        
        self._row('资产负债率', f"{self._safe_fmt(solvency.get('debt_to_assets'))}%")
        self._row('流动比率', self._safe_fmt(solvency.get('current_ratio')))
        
        self.pdf.ln(3)
        self._set_cn_font('B', 11)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.cell(0, 7, '现金流', ln=True)
        
        op_cf = cashflow.get('operating_cashflow')
        free_cf = cashflow.get('free_cashflow')
        self._row('经营现金流', f"{self._safe_fmt(op_cf, ',.0f')} 万")
        self._row('自由现金流', f"{self._safe_fmt(free_cf, ',.0f')} 万")
    
    def _render_valuation(self, data):
        """渲染估值分析"""
        valuation = data.get('valuation', {})
        if not valuation:
            return
        
        self._section_title(' 估值分析')
        
        current = valuation.get('current_valuation', {}) or {}
        hist = valuation.get('historical_percentile', {}) or {}
        
        total_mv = current.get('total_mv', 0)
        mv_str = f"{total_mv:.2f} 亿" if total_mv else '--'
        
        self._row('PE (TTM)', self._safe_fmt(current.get('pe_ttm')))
        self._row('PB', self._safe_fmt(current.get('pb')))
        self._row('PS', self._safe_fmt(current.get('ps')))
        self._row('总市值', mv_str)
        
        pe_pct = hist.get('pe_percentile')
        pb_pct = hist.get('pb_percentile')
        
        self.pdf.ln(3)
        self._set_cn_font('B', 11)
        self.pdf.set_text_color(80, 80, 80)
        self.pdf.cell(0, 7, '历史分位', ln=True)
        
        if pe_pct is not None:
            pe_label = '低估' if pe_pct < 30 else ('高估' if pe_pct > 70 else '合理')
            self._row('PE 分位', f"{self._safe_fmt(pe_pct, '.1f')}% ({pe_label})")
        
        if pb_pct is not None:
            pb_label = '低估' if pb_pct < 30 else ('高估' if pb_pct > 70 else '合理')
            self._row('PB 分位', f"{self._safe_fmt(pb_pct, '.1f')}% ({pb_label})")
        
        rating = valuation.get('rating', '')
        if rating:
            self.pdf.ln(2)
            self._set_cn_font('B', 11)
            self.pdf.set_text_color(30, 58, 95)
            self.pdf.cell(0, 8, f'估值评级: {rating}', ln=True)
    
    def _render_technical(self, data):
        """渲染技术面分析"""
        technical = data.get('technical', {})
        if not technical:
            return
        
        self._section_title('📉 技术面分析')
        
        score = technical.get('score', {}) or {}
        signals = technical.get('signals', {}) or {}
        
        if score:
            self._row('技术评分', f"{self._safe_fmt(score.get('total'), '.1f')} 分 ({score.get('rating', '--')})")
        
        signal_text = {
            'strong_buy': '强烈看多',
            'buy': '偏多',
            'sell': '偏空',
            'strong_sell': '强烈看空',
            'hold': '观望'
        }
        action = signals.get('action', 'hold')
        self._row('买卖信号', signal_text.get(action, '观望'))
        
        # 均线
        ma = technical.get('ma', {}) or {}
        if ma.get('values'):
            self.pdf.ln(3)
            self._set_cn_font('B', 11)
            self.pdf.set_text_color(80, 80, 80)
            arr_text = {
                'bullish': '多头排列',
                'bearish': '空头排列',
                'mixed': '交叉排列'
            }
            arrangement = ma.get('arrangement', '')
            self.pdf.cell(0, 7, f"均线 ({arr_text.get(arrangement, '--')})", ln=True)
            
            for period, value in ma.get('values', {}).items():
                self._row(f'MA{period}', self._safe_fmt(value))
    
    def _render_footer(self):
        """渲染页脚"""
        self.pdf.ln(10)
        self.pdf.set_draw_color(200, 200, 200)
        self.pdf.set_line_width(0.3)
        self.pdf.line(20, self.pdf.get_y(), 190, self.pdf.get_y())
        self.pdf.ln(5)
        
        self._set_cn_font('', 8)
        self.pdf.set_text_color(150, 150, 150)
        self.pdf.cell(0, 5, '本报告由智能股票深度分析平台自动生成，仅供参考，不构成投资建议。', ln=True, align='C')
        self.pdf.cell(0, 5, f'生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True, align='C')


# 全局单例
pdf_generator = StockReportPDF()
