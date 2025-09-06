"""
测试修复后的股票数据获取接口
"""

from api import get_stock_data
import pandas as pd

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试修复后的股票数据获取接口 ===")
    
    # 测试上证指数
    print("\n1. 测试上证指数 (000001)")
    try:
        data = get_stock_data('000001', 'sh', '2024-12-01', '2024-12-31')
        if data is not None and not data.empty:
            print(f"✅ 成功获取数据，形状: {data.shape}")
            print("列名:", data.columns.tolist())
            if '日期' in data.columns:
                print(f"日期范围: {data['日期'].min()} 到 {data['日期'].max()}")
            print("前3行数据:")
            print(data.head(3))
        else:
            print("❌ 获取数据失败")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    
    # 测试深证成指
    print("\n2. 测试深证成指 (399001)")
    try:
        data = get_stock_data('399001', 'sz', '2024-12-01', '2024-12-31')
        if data is not None and not data.empty:
            print(f"✅ 成功获取数据，形状: {data.shape}")
            print("列名:", data.columns.tolist())
        else:
            print("❌ 获取数据失败")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    
    # 测试美股
    print("\n3. 测试美股 (AAPL)")
    try:
        data = get_stock_data('AAPL', 'us', '2024-12-01', '2024-12-31')
        if data is not None and not data.empty:
            print(f"✅ 成功获取数据，形状: {data.shape}")
            print("列名:", data.columns.tolist())
        else:
            print("❌ 获取数据失败")
    except Exception as e:
        print(f"❌ 发生错误: {e}")

if __name__ == "__main__":
    test_basic_functionality()
    print("\n=== 测试完成 ===")
