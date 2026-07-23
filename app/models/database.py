"""数据库模型"""
from datetime import datetime
from app.extensions import db


class Watchlist(db.Model):
    """自选股模型"""
    __tablename__ = "watchlist"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False, unique=True, index=True)
    name = db.Column(db.String(50), default="")
    group_name = db.Column(db.String(50), default="默认")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "group": self.group_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnalysisReport(db.Model):
    """AI 分析报告模型"""
    __tablename__ = "analysis_reports"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False, index=True)
    report_date = db.Column(db.Date, nullable=False, index=True)
    report_text = db.Column(db.Text, default="")
    scores = db.Column(db.JSON, default=dict)  # 五维评分
    summary = db.Column(db.String(200), default="")
    rating = db.Column(db.String(20), default="")  # 强烈推荐/推荐/观望/回避
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "summary": self.summary,
            "rating": self.rating,
            "scores": self.scores,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
