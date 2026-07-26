"""
Gunicorn 生产环境配置
智能股票深度分析平台 - 端口 5005
"""

# 服务器 socket
bind = "0.0.0.0:5005"
backlog = 2048

# Worker 进程
workers = 4  # 建议：CPU 核心数 * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120  # 增加超时，股票分析可能较慢
keepalive = 2

# 进程命名
proc_name = "stock-analysis-platform"
daemon = False

# 日志
accesslog = "/root/.openclaw/workspace-fafaxia/projects/stock-analysis-platform/log/access.log"
errorlog = "/root/.openclaw/workspace-fafaxia/projects/stock-analysis-platform/log/error.log"
loglevel = "info"

# 预加载应用（节省内存）
preload_app = True

# 进程管理
max_requests = 1000  # worker 处理 1000 个请求后重启
max_requests_jitter = 50

# 临时文件
tmp_upload_dir = None

# 安全
limit_request_line = 4094
limit_request_field_size = 8190

# 统计
statsd_host = None
