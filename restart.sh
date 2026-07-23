#!/bin/bash
# 智能股票深度分析平台 - 重启脚本

set -e

# ==================== 配置 ====================
WORK_DIR="/root/.openclaw/workspace-fafaxia/projects/stock-analysis-platform"
PID_FILE="$WORK_DIR/.pid"
LOG_FILE="$WORK_DIR/.service.log"
PORT=5005

# ==================== 颜色 ====================
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ==================== 停止 ====================
stop_server() {
    info "停止服务 (端口 $PORT)..."

    # PID 文件
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            kill -0 "$pid" 2>/dev/null && kill -9 "$pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi

    # 端口查杀
    local port_pid=$(ss -tlnp 2>/dev/null | grep ":$PORT " | grep -oP 'pid=\K\d+' | head -1 || echo "")
    if [ -n "$port_pid" ]; then
        warn "端口 $PORT 仍被 PID $port_pid 占用，强制清理..."
        kill -9 "$port_pid" 2>/dev/null || true
        sleep 1
    fi

    ok "服务已停止"
}

# ==================== 启动 ====================
start_server() {
    info "启动服务 (端口 $PORT)..."
    cd "$WORK_DIR"

    nohup ./venv/bin/gunicorn \
        -w 2 \
        -b 0.0.0.0:$PORT \
        --access-logfile "$LOG_FILE" \
        --error-logfile "$LOG_FILE" \
        "app:create_app()" \
        > /dev/null 2>&1 &

    local pid=$!
    echo "$pid" > "$PID_FILE"
    info "PID: $pid"

    # 等待启动
    for i in $(seq 1 10); do
        sleep 1
        if ! kill -0 "$pid" 2>/dev/null; then
            error "进程已退出"
            tail -20 "$LOG_FILE"
            return 1
        fi
        if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
            ok "服务已启动 (第 ${i}s)"
            return 0
        fi
        echo "    等待中... ($i/10)"
    done

    error "启动超时"
    tail -20 "$LOG_FILE"
    return 1
}

# ==================== 状态 ====================
show_status() {
    echo ""
    echo "========================================"
    echo "📊 智能股票深度分析平台 - 状态"
    echo "========================================"
    echo ""

    local pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo -e "  服务 (:$PORT): ${GREEN}运行中${NC}  PID: $pid"
    else
        echo -e "  服务 (:$PORT): ${RED}未运行${NC}"
    fi

    local http=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/api/health 2>/dev/null || echo "000")
    if [ "$http" = "200" ]; then
        echo -e "  HTTP 检查:    ${GREEN}正常 ($http)${NC}"
    else
        echo -e "  HTTP 检查:    ${RED}异常 ($http)${NC}"
    fi

    echo ""
    echo "  访问地址: http://120.55.195.194:$PORT/"
    echo ""
    echo "========================================"
}

# ==================== 参数 ====================
case "${1:-}" in
    --status) show_status; exit 0 ;;
    --stop)   stop_server; exit 0 ;;
    --help|-h)
        echo "用法: $0 [--status|--stop|--help]"
        echo "  (无参数)  重启服务"
        echo "  --status  查看状态"
        echo "  --stop    停止服务"
        exit 0
        ;;
esac

# ==================== 主流程 ====================
echo ""
echo "========================================"
echo "📊 智能股票深度分析平台 - 重启"
echo "========================================"
echo ""

stop_server
echo ""
start_server

if [ $? -eq 0 ]; then
    echo ""
    echo "  ✅ 重启完成"
    echo "  访问: http://120.55.195.194:$PORT/"
    echo ""
fi
echo "========================================"
