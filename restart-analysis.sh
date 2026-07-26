#!/bin/bash
# 智能股票深度分析平台 - 一键重启脚本
# 参考 V6.0 脚本风格，增强稳定性和日志管理

echo "🔄 正在重启智能股票深度分析平台..."

# ==================== 配置 ====================
WORK_DIR="/root/.openclaw/workspace-fafaxia/projects/stock-analysis-platform"
PORT=5005
SERVICE_NAME="stock-analysis-platform"

# ==================== 颜色定义 ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ==================== 检查环境 ====================
cd "$WORK_DIR" || { error "无法进入工作目录: $WORK_DIR"; exit 1; }

# 检查虚拟环境
if [ ! -d "$WORK_DIR/venv" ]; then
    error "虚拟环境不存在: $WORK_DIR/venv"
    exit 1
fi

# 检查应用代码
if [ ! -f "$WORK_DIR/app/__init__.py" ]; then
    error "应用代码不存在: $WORK_DIR/app/__init__.py"
    exit 1
fi

# ==================== 停止服务 - 多重保障 ====================
echo ""
echo "⏹️  停止旧服务..."

# 步骤 1: 通过端口查找并终止（最可靠）
echo ""
echo "🔍 步骤 1: 检查端口 $PORT..."
PORT_PIDS=$(lsof -t -i:$PORT 2>/dev/null || true)
if [ -n "$PORT_PIDS" ]; then
    echo "📋 端口 $PORT 被占用，进程 ID: $PORT_PIDS"
    echo "⚡ 强制终止进程..."
    for pid in $PORT_PIDS; do
        kill -9 $pid 2>/dev/null || true
    done
    sleep 2
    
    # 再次检查
    PORT_PIDS2=$(lsof -t -i:$PORT 2>/dev/null || true)
    if [ -n "$PORT_PIDS2" ]; then
        warn "进程仍在运行，再次强制终止..."
        for pid in $PORT_PIDS2; do
            kill -9 $pid 2>/dev/null || true
        done
        sleep 2
    fi
fi

# 步骤 2: 通过 PID 文件查找并终止
echo ""
echo "🔍 步骤 2: 检查 PID 文件..."
if [ -f "$WORK_DIR/.pid" ]; then
    OLD_PID=$(cat $WORK_DIR/.pid 2>/dev/null || true)
    if [ -n "$OLD_PID" ]; then
        echo "📋 PID 文件中的进程 ID: $OLD_PID"
        kill -9 $OLD_PID 2>/dev/null || true
        sleep 1
        echo "✅ 已清理 PID 文件"
        rm -f $WORK_DIR/.pid
    fi
fi

# 步骤 3: 通过进程名查找并终止
echo ""
echo "🔍 步骤 3: 检查 Gunicorn/Flask 进程..."
GUNICORN_PIDS=$(ps aux | grep "[g]unicorn.*stock-analysis-platform" | awk '{print $2}' || true)
FLASK_PIDS=$(ps aux | grep "[f]lask run" | grep "port 5005" | awk '{print $2}' || true)

if [ -n "$GUNICORN_PIDS" ]; then
    echo "📋 找到 Gunicorn 进程: $GUNICORN_PIDS"
    echo "⚡ 强制终止..."
    for pid in $GUNICORN_PIDS; do
        kill -9 $pid 2>/dev/null || true
    done
    sleep 2
fi

if [ -n "$FLASK_PIDS" ]; then
    echo "📋 找到 Flask 进程: $FLASK_PIDS"
    echo "⚡ 强制终止..."
    for pid in $FLASK_PIDS; do
        kill -9 $pid 2>/dev/null || true
    done
    sleep 2
fi

# 步骤 4: 使用 fuser 释放端口（如果可用）
if command -v fuser > /dev/null 2>&1; then
    echo ""
    echo "🔧 步骤 4: 使用 fuser 检查端口 $PORT..."
    FUSER_PIDS=$(fuser $PORT/tcp 2>/dev/null || true)
    if [ -n "$FUSER_PIDS" ]; then
        echo "📋 fuser 找到进程: $FUSER_PIDS"
        fuser -k $PORT/tcp 2>/dev/null || true
        sleep 2
    fi
fi

# 步骤 5: 等待并验证
echo ""
echo "⏳ 步骤 5: 等待端口释放..."
sleep 3

# 最终验证
FINAL_CHECK=$(lsof -i:$PORT 2>/dev/null | wc -l || echo "0")
if [ "$FINAL_CHECK" -gt 0 ]; then
    warn "端口 $PORT 仍被占用，等待 5 秒..."
    sleep 5
    FINAL_CHECK=$(lsof -i:$PORT 2>/dev/null | wc -l || echo "0")
fi

if [ "$FINAL_CHECK" -gt 0 ]; then
    error "无法释放端口 $PORT，请手动检查:"
    lsof -i:$PORT 2>/dev/null || true
    exit 1
fi

ok "端口 $PORT 已释放"

# ==================== 日志管理 ====================
echo ""
echo "🗂️  日志管理..."

# 创建日志目录
mkdir -p $WORK_DIR/log

# 备份旧日志
if [ -f "$WORK_DIR/service.log" ]; then
    BACKUP_TIME=$(date +%Y%m%d_%H%M%S)
    mv "$WORK_DIR/service.log" "$WORK_DIR/log/service.log.old.$BACKUP_TIME"
    ok "旧日志已备份到: log/service.log.old.$BACKUP_TIME"
fi

# 清理超过 7 天的旧日志
find $WORK_DIR/log -name "service.log.old.*" -type f -mtime +7 -delete 2>/dev/null || true

# ==================== 启动服务 ====================
echo ""
echo "🚀 启动新服务..."

# 加载环境变量
if [ -f "$WORK_DIR/.env" ]; then
    set -a
    source "$WORK_DIR/.env"
    set +a
    info "已加载环境变量"
fi

# 激活虚拟环境并启动
source "$WORK_DIR/venv/bin/activate"

# 启动 Gunicorn 服务（生产环境）
if [ -f "$WORK_DIR/deploy/gunicorn.conf.py" ]; then
    info "使用 Gunicorn 启动（生产环境）..."
    nohup gunicorn -c deploy/gunicorn.conf.py "app:create_app()" > $WORK_DIR/service.log 2>&1 &
else
    warn "Gunicorn 配置不存在，使用 Flask 开发服务器..."
    nohup flask run --host 0.0.0.0 --port $PORT > $WORK_DIR/service.log 2>&1 &
fi
NEW_PID=$!
echo $NEW_PID > $WORK_DIR/.pid

info "服务已启动，PID: $NEW_PID"
info "日志文件: $WORK_DIR/service.log"

# ==================== 等待启动 ====================
echo ""
echo "⏳ 等待服务启动..."

SUCCESS=false
for i in {1..30}; do
    sleep 1
    
    # 检查 1: HTTP 健康检查（最可靠）
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/ 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        ok "HTTP 检查通过 (第 ${i}s)"
        SUCCESS=true
        break
    fi
    
    # 检查 2: 端口是否监听
    PORT_CHECK=$(ss -tlnp 2>/dev/null | grep ":$PORT " | wc -l || echo "0")
    if [ "$PORT_CHECK" -gt 0 ]; then
        ok "端口 $PORT 已监听 (第 ${i}s)"
        SUCCESS=true
        break
    fi
    
    # 检查进程是否存在
    if ! ps -p $NEW_PID > /dev/null 2>&1; then
        error "进程已退出，启动失败"
        echo ""
        echo "错误日志:"
        echo "----------------------------------------"
        tail -30 $WORK_DIR/service.log
        echo "----------------------------------------"
        exit 1
    fi
    
    # 每 5 秒显示进度
    if [ $((i % 5)) -eq 0 ]; then
        echo "  等待中... ($i/30)"
    fi
done

# ==================== 健康检查 ====================
echo ""
echo "🔍 验证服务状态..."

if [ "$SUCCESS" = false ]; then
    error "服务启动超时！"
    echo ""
    echo "最近日志:"
    echo "----------------------------------------"
    tail -30 $WORK_DIR/service.log
    echo "----------------------------------------"
    exit 1
fi

# 最终 HTTP 健康检查
HTTP_FINAL=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/ 2>/dev/null || echo "000")
if [ "$HTTP_FINAL" = "200" ] || [ "$HTTP_FINAL" = "302" ]; then
    ok "HTTP 健康检查通过 (状态码: $HTTP_FINAL)"
else
    warn "HTTP 状态码: $HTTP_FINAL"
fi

# ==================== 显示状态 ====================
echo ""
echo "========================================"
ok "智能股票深度分析平台已成功重启！"
echo "========================================"
echo ""
echo "📊 服务信息:"
echo "  ✅ 服务名称: $SERVICE_NAME"
echo "  ✅ 进程 PID: $NEW_PID"
echo "  ✅ 监听端口: $PORT"
echo "  ✅ 访问地址: http://localhost:$PORT"
echo "  ✅ 日志目录: $WORK_DIR/log/"
echo ""
echo "📋 最近日志 (最后 10 行):"
echo "----------------------------------------"
tail -10 $WORK_DIR/service.log 2>/dev/null || echo "(日志文件为空，服务正在初始化)"
echo "----------------------------------------"
echo ""
echo "💡 提示:"
echo "  - 查看实时日志: tail -f $WORK_DIR/service.log"
echo "  - 查看历史日志: ls -lh $WORK_DIR/log/"
echo "  - 停止服务:     pkill -f 'gunicorn.*stock-analysis-platform'"
echo ""
