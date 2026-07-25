"""
PDF 报告生成服务（美化版）

使用 fpdf2 生成 PDF 分析报告，支持中文，精美排版
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any
from fpdf import FPDF

logger = logging.getLogger(__name__)

FONT_DIR = '/usr/share/fonts'
CN_FONT_PATH = os.path.join(FONT_DIR, 'NotoSansSC-Regular.ttf')

# 配色方案
COLOR = {
    'primary': (30, 58, 95),       # 深蓝 - 主标题
    'secondary': (59, 130, 246),   # 亮蓝 - 副标题/链接
    'accent': (245, 158, 11),      # 橙色 - 警告/中等
    'success': (34, 197, 94),      # 绿色 - 正面/上涨
    'danger': (239, 68, 68),       # 红色 - 负面/下跌
    'text': (50, 50, 50),          # 深灰 - 正文
    'text_light': (100, 100, 100), # 中灰 - 次要文字
    'text_lighter': (150, 150, 150), # 浅灰 - 辅助文字
    'border': (200, 200, 200),     # 边框
    'bg_header': (245, 247, 250),  # 浅蓝背景
    'bg_card': (252, 253, 255),    # 卡片背景
}


class StockReportPDF:
    """股票分析报告 PDF 生成器（美化版）"""
    
    def __init__(self):
        self._load_font()
    
    def _load_font(self):
        if os.path.exists(CN_FONT_PATH):
            self.pdf = FPDF()
            self.pdf.add_font('NotoSansSC', '', CN_FONT_PATH, uni=True)
            self.pdf.add_font('NotoSansSC', 'B', CN_FONT_PATH, uni=True)
        else:
            logger.warning(f"中文字体不存在：{CN_FONT_PATH}")
            self.pdf = FPDF()
    
    def _reset_pdf(self):
        self.pdf = FPDF()
        if os.path.exists(CN_FONT_PATH):
            self.pdf.add_font('NotoSansSC', '', CN_FONT_PATH, uni=True)
            self.pdf.add_font('NotoSansSC', 'B', CN_FONT_PATH, uni=True)
    
    def _set_font(self, style='', size=12, color=None):
        font_name = 'NotoSansSC' if os.path.exists(CN_FONT_PATH) else 'Helvetica'
        self.pdf.set_font(font_name, style, size)
        if color:
            self.pdf.set_text_color(*color)
    
    def _safe_text(self, text) -> str:
        if text is None:
            return ''
        return str(text).replace('\r', '').replace('\x00', '')
    
    def _safe_fmt(self, value, fmt_str='.2f', default='--'):
        if value is None:
            return default
        try:
            return format(float(value), fmt_str)
        except:
            return default
    
    def _color_for_value(self, value, zero_is_neutral=True):
        """根据数值正负返回颜色"""
        if value is None:
            return COLOR['text_light']
        if zero_is_neutral and value == 0:
            return COLOR['text_light']
        return COLOR['success'] if value > 0 else COLOR['danger']
    
    def _section_header(self, icon: str, title: str):
        """渲染章节标题（带图标和背景）"""
        self.pdf.ln(6)
        # 背景条
        y = self.pdf.get_y()
        self.pdf.set_fill_color(*COLOR['bg_header'])
        self.pdf.rect(15, y - 2, 180, 12, 'F')
        
        self._set_font('B', 14, COLOR['primary'])
        self.pdf.set_xy(18, y)
        self.pdf.cell(0, 10, f'{icon}  {self._safe_text(title)}', ln=True)
        self.pdf.ln(2)
    
    def _subsection(self, title: str):
        """渲染小节标题"""
        self.pdf.ln(2)
        self._set_font('B', 11, COLOR['secondary'])
        self.pdf.cell(0, 7, self._safe_text(title), ln=True)
    
    def _data_row(self, label: str, value: str, value_color=None, bold_value=False):
        """渲染数据行（双栏布局）"""
        # 标签
        self._set_font('', 10, COLOR['text_light'])
        self.pdf.cell(70, 7, self._safe_text(label))
        
        # 值
        style = 'B' if bold_value else ''
        self._set_font(style, 10, value_color or COLOR['text'])
        self.pdf.cell(0, 7, self._safe_text(value), ln=True)
    
    def _data_row_highlight(self, label: str, value, unit='', fmt='.2f'):
        """渲染高亮数据行（值带颜色判断）"""
        val_color = self._color_for_value(value)
        val_str = self._safe_fmt(value, fmt) + unit if value is not None else '--'
        self._data_row(label, val_str, val_color, bold_value=True)
    
    def _card_box(self, title: str, content_lines: list, bg_color=COLOR['bg_card']):
        """渲染卡片式信息块"""
        y_start = self.pdf.get_y()
        # 检查是否需要新页
        if y_start > 250:
            self.pdf.add_page()
            y_start = self.pdf.get_y()
        
        # 卡片背景
        self.pdf.set_fill_color(*bg_color)
        box_h = 8 + len(content_lines) * 8
        self.pdf.rect(15, y_start, 180, box_h, 'F')
        
        # 卡片标题
        self.pdf.set_xy(18, y_start + 2)
        self._set_font('B', 10, COLOR['primary'])
        self.pdf.cell(0, 6, self._safe_text(title))
        
        # 卡片内容
        self.pdf.set_x(18)
        self._set_font('', 9, COLOR['text'])
        for line in content_lines:
            self.pdf.cell(0, 7, self._safe_text(line), ln=True)
        
        self.pdf.set_y(y_start + box_h + 3)
    
    def generate(self, data: Dict[str, Any]) -> str:
        self._reset_pdf()
        
        code = data.get('code', '')
        name = data.get('name', code)
        
        self.pdf.add_page()
        self._render_header(name, code, data)
        self._render_score(data)
        self._render_fundamental(data)
        self._render_valuation(data)
        self._render_technical(data)
        self._render_dupont(data)
        self._render_capital(data)
        self._render_industry(data)
        self._render_footer()
        
        output_dir = '/root/.openclaw/workspace-fafaxia/projects/stock-analysis-platform/reports'
        os.makedirs(output_dir, exist_ok=True)
        filename = f"report_{code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(output_dir, filename)
        self.pdf.output(filepath)
        
        logger.info(f"✓ PDF 报告已生成：{filepath}")
        return filepath
    
    def _render_header(self, name, code, data):
        """报告头部"""
        # 顶部色块
        self.pdf.set_fill_color(*COLOR['primary'])
        self.pdf.rect(0, 0, 210, 45, 'F')
        
        self.pdf.set_xy(0, 10)
        self._set_font('B', 24, (255, 255, 255))
        self.pdf.cell(0, 12, f'{self._safe_text(name)}  ({code})', ln=True, align='C')
        
        self.pdf.set_xy(0, 26)
        self._set_font('', 11, (200, 220, 240))
        self.pdf.cell(0, 8, f'股票深度分析报告  |  {datetime.now().strftime("%Y-%m-%d")}', ln=True, align='C')
        
        self.pdf.set_y(52)
        
        # 股票基本信息卡片
        score_data = data.get('score', {})
        total = score_data.get('total_score', 0) or 0
        rating = score_data.get('rating', '--') or '--'
        fundamental = data.get('fundamental', {})
        profitability = fundamental.get('profitability', {}) or {}
        
        # 评分卡片
        score_color = COLOR['success'] if total >= 70 else (COLOR['secondary'] if total >= 50 else (COLOR['accent'] if total >= 30 else COLOR['danger']))
        self._set_font('B', 11, COLOR['text_light'])
        self.pdf.cell(45, 7, '综合评分')
        self._set_font('B', 20, score_color)
        self.pdf.cell(40, 12, f'{total:.1f}', align='C')
        self._set_font('B', 11, score_color)
        self.pdf.cell(0, 7, f' 评级：{rating}', ln=True)
        
        # ROE
        roe = profitability.get('roe')
        self._set_font('', 10, COLOR['text_light'])
        self.pdf.cell(45, 7, 'ROE')
        if roe is not None:
            roe_color = self._color_for_value(roe)
            self._set_font('B', 14, roe_color)
            self.pdf.cell(0, 10, f'{roe:.2f}%', ln=True)
        else:
            self._set_font('', 14, COLOR['text_lighter'])
            self.pdf.cell(0, 10, '--', ln=True)
        
        self.pdf.ln(3)
    
    def _render_score(self, data):
        score_data = data.get('score', {})
        if not score_data:
            return
        
        self._section_header('📊', '综合评分')
        
        breakdown = score_data.get('breakdown', {})
        dim_info = [
            ('fundamental_score', '基本面', '📋'),
            ('technical_score', '技术面', '📈'),
            ('valuation_score', '估值面', '💰'),
            ('capital_score', '资金面', '💵'),
            ('industry_score', '行业面', ''),
            ('growth_score', '成长性', '🌱'),
        ]
        
        for key, label, icon in dim_info:
            val = breakdown.get(key)
            if val is not None:
                color = COLOR['success'] if val >= 70 else (COLOR['secondary'] if val >= 50 else (COLOR['accent'] if val >= 30 else COLOR['danger']))
                self._data_row(f'{icon} {label}', f'{val:.1f} 分', color, bold_value=True)
            else:
                self._data_row(f'{icon} {label}', '--')
    
    def _render_fundamental(self, data):
        fundamental = data.get('fundamental', {})
        if not fundamental:
            return
        
        self._section_header('📋', '基本面分析')
        
        profitability = fundamental.get('profitability', {}) or {}
        growth = fundamental.get('growth', {}) or {}
        solvency = fundamental.get('solvency', {}) or {}
        cashflow = fundamental.get('cashflow', {}) or {}
        
        self._subsection('盈利能力')
        self._data_row_highlight('ROE', profitability.get('roe'), '%')
        self._data_row_highlight('净利率', profitability.get('net_margin'), '%')
        self._data_row_highlight('毛利率', profitability.get('gross_margin'), '%')
        self._data_row('EPS', self._safe_fmt(profitability.get('eps')) + ' 元', COLOR['text'], True)
        
        self._subsection('成长性')
        rev_yoy = growth.get('revenue_yoy')
        profit_yoy = growth.get('profit_yoy')
        self._data_row_highlight('营收同比', rev_yoy, '%')
        self._data_row_highlight('利润同比', profit_yoy, '%')
        continuous = growth.get('profit_continuous_growth_quarters')
        if continuous is not None:
            self._data_row('连续增长季度', f'{int(continuous)} 季', COLOR['secondary'], True)
        
        self._subsection('偿债能力')
        self._data_row_highlight('资产负债率', solvency.get('debt_to_assets'), '%')
        self._data_row('流动比率', self._safe_fmt(solvency.get('current_ratio')), COLOR['text'], True)
        
        self._subsection('现金流')
        op_cf = cashflow.get('operating_cashflow')
        free_cf = cashflow.get('free_cashflow')
        if op_cf is not None:
            self._data_row('经营现金流', f'{int(op_cf):,} 万', self._color_for_value(op_cf), True)
        if free_cf is not None:
            self._data_row('自由现金流', f'{int(free_cf):,} 万', self._color_for_value(free_cf), True)
    
    def _render_valuation(self, data):
        valuation = data.get('valuation', {})
        if not valuation:
            return
        
        self._section_header('💰', '估值分析')
        
        current = valuation.get('current_valuation', {}) or {}
        hist = valuation.get('historical_percentile', {}) or {}
        
        self._subsection('当前估值')
        self._data_row('PE (TTM)', self._safe_fmt(current.get('pe_ttm')), COLOR['text'], True)
        self._data_row('PB', self._safe_fmt(current.get('pb')), COLOR['text'], True)
        self._data_row('PS', self._safe_fmt(current.get('ps')), COLOR['text'], True)
        
        total_mv = current.get('total_mv')
        if total_mv:
            self._data_row('总市值', f'{total_mv:.2f} 亿', COLOR['text'], True)
        
        self._subsection('历史分位')
        pe_pct = hist.get('pe_percentile')
        pb_pct = hist.get('pb_percentile')
        
        if pe_pct is not None:
            pe_color = COLOR['success'] if pe_pct < 30 else (COLOR['danger'] if pe_pct > 70 else COLOR['accent'])
            pe_label = '低估' if pe_pct < 30 else ('高估' if pe_pct > 70 else '合理')
            self._data_row('PE 分位', f'{pe_pct:.1f}% ({pe_label})', pe_color, True)
        
        if pb_pct is not None:
            pb_color = COLOR['success'] if pb_pct < 30 else (COLOR['danger'] if pb_pct > 70 else COLOR['accent'])
            pb_label = '低估' if pb_pct < 30 else ('高估' if pb_pct > 70 else '合理')
            self._data_row('PB 分位', f'{pb_pct:.1f}% ({pb_label})', pb_color, True)
        
        # 估值评级
        rating = valuation.get('rating', '')
        if rating:
            self.pdf.ln(3)
            rating_color = COLOR['success'] if '低估' in rating else (COLOR['danger'] if '高估' in rating else COLOR['accent'])
            self._set_font('B', 12, rating_color)
            self.pdf.cell(0, 10, f'估值评级：{rating}', ln=True)
    
    def _render_technical(self, data):
        technical = data.get('technical', {})
        if not technical:
            return
        
        self._section_header('📈', '技术面分析')
        
        score = technical.get('score', {}) or {}
        signals = technical.get('signals', {}) or {}
        
        if score:
            total = score.get('total', 0)
            color = COLOR['success'] if total >= 70 else (COLOR['secondary'] if total >= 50 else (COLOR['accent'] if total >= 30 else COLOR['danger']))
            self._data_row('技术评分', f"{self._safe_fmt(total, '.1f')} 分 ({score.get('rating', '--')})", color, True)
        
        signal_text = {
            'strong_buy': '强烈看多', 'buy': '偏多', 'sell': '偏空',
            'strong_sell': '强烈看空', 'hold': '观望'
        }
        action = signals.get('action', 'hold')
        action_color = COLOR['success'] if action in ('strong_buy', 'buy') else (COLOR['danger'] if action in ('strong_sell', 'sell') else COLOR['accent'])
        self._data_row('买卖信号', signal_text.get(action, '观望'), action_color, True)
        
        # 看多/看空数量
        bullish = signals.get('bullish_count', 0)
        bearish = signals.get('bearish_count', 0)
        if bullish or bearish:
            self._data_row('信号明细', f'看多 {bullish} / 看空 {bearish}', COLOR['text_light'])
        
        ma = technical.get('ma', {}) or {}
        if ma.get('values'):
            self._subsection('均线系统')
            arr_text = {'bullish': '多头排列 ↑', 'bearish': '空头排列 ↓', 'mixed': '交叉排列 ↔'}
            arrangement = ma.get('arrangement', '')
            arr_color = COLOR['success'] if arrangement == 'bullish' else (COLOR['danger'] if arrangement == 'bearish' else COLOR['accent'])
            self._data_row('排列状态', arr_text.get(arrangement, '--'), arr_color, True)
            
            for period, value in ma.get('values', {}).items():
                self._data_row(f'MA{period}', self._safe_fmt(value), COLOR['text'])
    
    def _render_dupont(self, data):
        dupont = data.get('dupont', {})
        if not dupont:
            return
        
        self._section_header('🔍', '杜邦分析')
        
        current = dupont.get('current', {}) or {}
        contribution = dupont.get('contribution', {}) or {}
        
        roe = current.get('roe')
        if roe is not None:
            self._set_font('B', 12, COLOR['primary'])
            self.pdf.cell(0, 10, f'ROE (净资产收益率): {roe:.2f}%', ln=True)
        
        self._subsection('三因素分解')
        self._data_row_highlight('净利率', current.get('net_profit_margin'), '%')
        self._data_row('总资产周转率', self._safe_fmt(current.get('asset_turnover')), COLOR['text'], True)
        self._data_row('权益乘数', self._safe_fmt(current.get('equity_multiplier')), COLOR['text'], True)
        
        # 公式
        self.pdf.ln(2)
        self._set_font('', 10, COLOR['text_light'])
        nm = current.get('net_profit_margin')
        at = current.get('asset_turnover')
        em = current.get('equity_multiplier')
        if nm is not None and at is not None and em is not None:
            self.pdf.cell(0, 7, f'ROE = 净利率 × 资产周转率 × 权益乘数', ln=True)
            self.pdf.cell(0, 7, f'    = {nm:.2f}% × {at:.2f} × {em:.2f}', ln=True)
        
        # 主要驱动因素
        main_driver = contribution.get('main_driver')
        if main_driver:
            self.pdf.ln(2)
            self._data_row('主要驱动因素', main_driver, COLOR['secondary'], True)
        
        # 趋势
        trend = dupont.get('trend', {}) or {}
        if trend:
            self._subsection('趋势变化')
            net_trend = trend.get('net_margin_trend', '')
            if net_trend:
                net_color = COLOR['danger'] if net_trend == '↓' else COLOR['success']
                self._data_row('净利率趋势', net_trend, net_color, True)
            at_trend = trend.get('asset_turn_trend', '')
            if at_trend:
                at_color = COLOR['danger'] if at_trend == '↓' else COLOR['success']
                self._data_row('资产周转率趋势', at_trend, at_color, True)
            em_trend = trend.get('equity_multiplier_trend', '')
            if em_trend:
                em_color = COLOR['danger'] if em_trend == '↓' else COLOR['success']
                self._data_row('权益乘数趋势', em_trend, em_color, True)
    
    def _render_capital(self, data):
        capital = data.get('capital', {})
        if not capital:
            return
        
        self._section_header('💵', '资金面分析')
        
        money_flow = capital.get('money_flow', {}) or {}
        north_flow = capital.get('north_flow', {}) or {}
        margin = capital.get('margin', {}) or {}
        chip_dist = capital.get('chip_distribution', {}) or {}
        capital_score = capital.get('capital_score', {}) or {}
        
        # 资金面评分
        if capital_score:
            total = capital_score.get('total')
            if total is not None:
                color = COLOR['success'] if total >= 70 else (COLOR['secondary'] if total >= 50 else (COLOR['accent'] if total >= 30 else COLOR['danger']))
                self._data_row('资金面评分', f"{self._safe_fmt(total, '.1f')} 分 ({capital_score.get('rating', '--')})", color, True)
        
        self._subsection('主力资金流向')
        main_net = money_flow.get('main_net_inflow')
        if main_net is not None:
            self._data_row('主力净流入', f'{int(main_net):,} 万', self._color_for_value(main_net), True)
        
        main_pct = money_flow.get('main_net_inflow_pct')
        if main_pct is not None:
            self._data_row('主力占比', f'{main_pct:.2f}%', self._color_for_value(main_pct))
        
        trend = money_flow.get('trend', '')
        if trend:
            trend_color = COLOR['success'] if '流入' in trend else (COLOR['danger'] if '流出' in trend else COLOR['text'])
            self._data_row('资金趋势', trend, trend_color, True)
        
        self._subsection('北向资金')
        north_hold = north_flow.get('hold_ratio')
        if north_hold:
            self._data_row('北向持股比例', f'{north_hold:.2f}%', COLOR['text'], True)
        
        self._subsection('融资融券')
        margin_balance = margin.get('margin_balance')
        if margin_balance:
            self._data_row('融资余额', f'{int(margin_balance):,} 万', COLOR['text'], True)
        net_margin = margin.get('net_margin')
        if net_margin is not None:
            self._data_row('融资净买入', f'{int(net_margin):,} 万', self._color_for_value(net_margin), True)
        
        self._subsection('筹码分布')
        concentration = chip_dist.get('concentration')
        if concentration:
            self._data_row('筹码集中度', concentration, COLOR['text'], True)
        profit_ratio = chip_dist.get('profit_ratio')
        if profit_ratio is not None:
            self._data_row('获利盘比例', f'{profit_ratio:.2f}%', COLOR['success'] if profit_ratio > 50 else COLOR['danger'])
        price_pos = chip_dist.get('price_position')
        if price_pos:
            pos_color = COLOR['danger'] if '高' in price_pos else (COLOR['success'] if '低' in price_pos else COLOR['accent'])
            self._data_row('股价位置', price_pos, pos_color, True)
    
    def _render_industry(self, data):
        industry = data.get('industry', {})
        if not industry:
            return
        
        self._section_header('🏭', '行业面分析')
        
        industry_info = industry.get('industry_info', {}) or {}
        industry_score = industry.get('industry_score', {}) or {}
        industry_trend = industry.get('industry_trend', {}) or {}
        
        if industry_score:
            total = industry_score.get('total')
            if total is not None:
                color = COLOR['success'] if total >= 70 else (COLOR['secondary'] if total >= 50 else (COLOR['accent'] if total >= 30 else COLOR['danger']))
                self._data_row('行业面评分', f"{self._safe_fmt(total, '.1f')} 分 ({industry_score.get('rating', '--')})", color, True)
        
        industry_name = industry_info.get('industry_name')
        if industry_name:
            self._data_row('所属行业', industry_name, COLOR['secondary'], True)
        
        market_pos = industry_info.get('market_position')
        if market_pos:
            self._data_row('市场地位', market_pos, COLOR['text'], True)
        
        trend = industry_trend.get('trend')
        if trend:
            trend_color = COLOR['success'] if trend == '热门' else (COLOR['danger'] if trend == '冷门' else COLOR['accent'])
            self._data_row('行业趋势', trend, trend_color, True)
        
        # 概念标签
        concept_tags = industry.get('concept_tags', {}) or {}
        tags = concept_tags.get('tags', [])
        if tags:
            self._subsection('所属概念')
            self._set_font('', 10, COLOR['secondary'])
            tag_text = '、'.join(tags[:8])
            self.pdf.cell(0, 7, tag_text, ln=True)
    
    def _render_footer(self):
        self.pdf.ln(8)
        self.pdf.set_draw_color(*COLOR['border'])
        self.pdf.set_line_width(0.3)
        self.pdf.line(20, self.pdf.get_y(), 190, self.pdf.get_y())
        self.pdf.ln(4)
        
        self._set_font('', 8, COLOR['text_lighter'])
        self.pdf.cell(0, 5, '本报告由智能股票深度分析平台自动生成，仅供参考，不构成投资建议。', ln=True, align='C')
        self.pdf.cell(0, 5, f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True, align='C')


# 全局单例
pdf_generator = StockReportPDF()
