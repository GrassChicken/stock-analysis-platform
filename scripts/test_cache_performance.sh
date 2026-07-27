#!/bin/bash
# 缓存性能测试脚本

STOCK_CODE="600519"
BASE_URL="http://localhost:5005/api/stock"

echo "=========================================="
echo "缓存性能测试 - 智能股票深度分析平台"
echo "=========================================="
echo ""

test_endpoint() {
    local name=$1
    local endpoint=$2
    local url="${BASE_URL}/${STOCK_CODE}/${endpoint}"
    
    echo "测试: $name"
    echo "URL: $url"
    echo "------------------------------------------"
    
    # 第一次请求（未缓存）
    time1=$(curl -s -o /dev/null -w "%{time_total}" "$url")
    echo "第1次请求: ${time1}s"
    
    sleep 0.5
    
    # 第二次请求（应该命中缓存）
    time2=$(curl -s -o /dev/null -w "%{time_total}" "$url")
    echo "第2次请求: ${time2}s"
    
    sleep 0.5
    
    # 第三次请求（应该命中缓存）
    time3=$(curl -s -o /dev/null -w "%{time_total}" "$url")
    echo "第3次请求: ${time3}s"
    
    # 计算性能提升
    improvement=$(echo "scale=1; (($time1 - $time3) / $time1) * 100" | bc 2>/dev/null || echo "N/A")
    echo "性能提升: ${improvement}%"
    echo ""
}

# 测试各个接口
test_endpoint "基本面分析" "fundamental"
test_endpoint "估值分析" "valuation"
test_endpoint "杜邦分析" "dupont"
test_endpoint "技术面分析" "technical"
test_endpoint "资金面分析" "capital"
test_endpoint "行业面分析" "industry"
test_endpoint "AI 智能分析" "ai"
test_endpoint "综合评分" "score"

echo "=========================================="
echo "测试完成"
echo "=========================================="
