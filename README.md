# 智能股票深度分析平台

> Python 3.11 + Flask + Tailwind CSS + HTMX + ECharts

个股深度分析工具，支持基本面/技术面/资金面/估值面/行业面五维分析 + AI 智能解读。

## 快速启动

```bash
# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 启动开发服务
flask run --port 5005

# 或生产部署
gunicorn -w 2 -b 0.0.0.0:5005 "app:create_app()"
```

## 项目结构

```
app/
├── routes/         # 路由层
├── services/       # 业务逻辑层
│   ├── data/       #   数据获取 (pytdx/akshare)
│   ├── analysis/   #   分析引擎
│   └── utils/      #   工具函数
├── models/         # 数据模型
├── templates/      # Jinja2 模板
└── static/         # 静态资源
```

## 文档

- [架构设计](ARCHITECTURE.md)
- [开发计划](DEVELOPMENT_PLAN.md)
