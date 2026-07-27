#!/usr/bin/env python3
"""测试缓存性能"""
import requests
import time
import sys

def test_endpoint(name, url, repeat=3):
    """测试单个接口的缓存效果"""
    print(f"\n{'='*60}")
    print(f"测试接口: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    times = []
    for i in range(repeat):
        start = time.time()
        response = requests.get(url)
        elapsed = time.time() - start
        times.append(elapsed)
        
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} 第{i+1}次请求: {elapsed:.3f}秒 (状态码: {response.status_code})")
        
        if i == 0:
            print(f"  → 首次请求（未缓存）")
        else:
            print(f"  → 后续请求（已缓存）")
        
        time.sleep(0.5)  # 短暂间隔
    
    # 统计
    avg_time = sum(times) / len(times)
    first_time = times[0]
    cached_times = times[1:]
    avg_cached = sum(cached_times) / len(cached_times) if cached_times else 0
    
    print(f"\n统计结果:")
    print(f"  平均响应时间: {avg_time:.3f}秒")
    print(f"  首次响应时间: {first_time:.3f}秒")
    if cached_times:
        print(f"  缓存后平均时间: {avg_cached:.3f}秒")
        improvement = ((first_time - avg_cached) / first_time * 100) if first_time > 0 else 0
        print(f"  性能提升: {improvement:.1f}%")

def main():
    base_url = "http://localhost:5005"
    test_stock = "600519"  # 贵州茅台
    
    print("="*60)
    print("缓存性能测试 - 智能股票深度分析平台")
    print("="*60)
    
    # 测试各个分析接口
    endpoints = [
        ("基本面分析", f"{base_url}/api/stock/{test_stock}/fundamental"),
        ("估值分析", f"{base_url}/api/stock/{test_stock}/valuation"),
        ("杜邦分析", f"{base_url}/api/stock/{test_stock}/dupont"),
        ("技术面分析", f"{base_url}/api/stock/{test_stock}/technical"),
        ("资金面分析", f"{base_url}/api/stock/{test_stock}/capital"),
        ("行业面分析", f"{base_url}/api/stock/{test_stock}/industry"),
        ("AI 智能分析", f"{base_url}/api/stock/{test_stock}/ai"),
        ("综合评分", f"{base_url}/api/stock/{test_stock}/score"),
    ]
    
    for name, url in endpoints:
        try:
            test_endpoint(name, url, repeat=3)
        except Exception as e:
            print(f"\n✗ 测试失败: {name}")
            print(f"  错误: {str(e)}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    main()
