"""知识百科路由 - 股票指标解释"""
from flask import Blueprint, render_template

knowledge_bp = Blueprint("knowledge", __name__)


@knowledge_bp.route("/knowledge")
def knowledge_index():
    """指标百科主页"""
    return render_template("pages/knowledge.html", title="📖 指标百科")
