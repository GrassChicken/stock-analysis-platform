"""深度分析路由"""
from flask import Blueprint, render_template

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/stock/<code>")
def stock_analysis(code: str):
    """个股深度分析页 - 核心页面"""
    return render_template(
        "pages/analysis.html",
        stock_code=code,
        title=f"深度分析 - {code}",
    )


@analysis_bp.route("/compare")
def compare():
    """对比 PK 页"""
    return render_template("pages/compare.html", title="股票对比")
