
"""
股票数据获取接口使用示例
支持上证、深证、创业板、美股数据获取
"""

from api import StockDataAPI, get_stock_data, get_market_list, get_realtime_data
import pandas as pd
from datetime import datetime, timedelta


def main():
    """主函数：演示各种数据获取功能"""
    
    # 创建API实例
    api = StockDataAPI()
    
    print("=" * 60)
    print("股票数据获取接口使用示例")
    print("=" * 60)
    
    # 1. 获取上证指数数据
    print("\n1. 获取上证指数数据 (000001)")
    print("-" * 40)
    sh_data = get_stock_data(
        symbol='000001',
        market='sh',
        start_date='2024-01-01',
        end_date='2024-12-31',
        period='daily',
        adjust='qfq'
    )
    
    if sh_data is not None and not sh_data.empty:
        print(f"数据形状: {sh_data.shape}")
        print("前5行数据:")
        print(sh_data.head())
        # 安全地获取日期范围
        if '日期' in sh_data.columns:
            print(f"数据时间范围: {sh_data['日期'].min()} 到 {sh_data['日期'].max()}")
        else:
            print("可用列名:", sh_data.columns.tolist())
    else:
        print("获取数据失败")
    
    # 2. 获取深证成指数据
    print("\n2. 获取深证成指数据 (399001)")
    print("-" * 40)
    sz_data = get_stock_data(
        symbol='399001',
        market='sz',
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    if sz_data is not None and not sz_data.empty:
        print(f"数据形状: {sz_data.shape}")
        print("前5行数据:")
        print(sz_data.head())
    else:
        print("获取数据失败")
    
    # 3. 获取创业板指数据
    print("\n3. 获取创业板指数据 (399006)")
    print("-" * 40)
    cyb_data = get_stock_data(
        symbol='399006',
        market='cyb',
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    if cyb_data is not None and not cyb_data.empty:
        print(f"数据形状: {cyb_data.shape}")
        print("前5行数据:")
        print(cyb_data.head())
    else:
        print("获取数据失败")
    
    # 4. 获取美股数据（苹果公司）
    print("\n4. 获取美股数据（苹果公司 AAPL）")
    print("-" * 40)
    us_data = get_stock_data(
        symbol='AAPL',
        market='us',
        start_date='2024-01-01',
        end_date='2024-12-31'
    )
    
    if us_data is not None and not us_data.empty:
        print(f"数据形状: {us_data.shape}")
        print("前5行数据:")
        print(us_data.head())
    else:
        print("获取数据失败")
    
    # 5. 获取不同周期的数据
    print("\n5. 获取周线数据（上证指数）")
    print("-" * 40)
    weekly_data = get_stock_data(
        symbol='000001',
        market='sh',
        start_date='2024-01-01',
        end_date='2024-12-31',
        period='weekly'
    )
    
    if weekly_data is not None and not weekly_data.empty:
        print(f"周线数据形状: {weekly_data.shape}")
        print("前5行数据:")
        print(weekly_data.head())
    else:
        print("获取数据失败")
    
    # 6. 获取市场股票列表
    print("\n6. 获取上证A股列表")
    print("-" * 40)
    sh_list = get_market_list('sh')
    
    if sh_list is not None and not sh_list.empty:
        print(f"上证A股数量: {len(sh_list)}")
        print("前10只股票:")
        # 安全地选择列
        available_cols = ['代码', '名称', '最新价', '涨跌幅', '涨跌额']
        display_cols = [col for col in available_cols if col in sh_list.columns]
        if display_cols:
            print(sh_list.head(10)[display_cols])
        else:
            print("可用列名:", sh_list.columns.tolist())
            print(sh_list.head(10))
    else:
        print("获取列表失败")
    
    # 7. 获取实时数据
    print("\n7. 获取实时数据（上证指数）")
    print("-" * 40)
    realtime_data = get_realtime_data('000001', 'sh')
    
    if realtime_data is not None and not realtime_data.empty:
        print("实时数据:")
        # 安全地选择列
        available_cols = ['代码', '名称', '最新价', '涨跌幅', '涨跌额', '成交量', '成交额']
        display_cols = [col for col in available_cols if col in realtime_data.columns]
        if display_cols:
            print(realtime_data[display_cols])
        else:
            print("可用列名:", realtime_data.columns.tolist())
            print(realtime_data)
    else:
        print("获取实时数据失败")
    
    # 8. 批量获取多只股票数据
    print("\n8. 批量获取多只股票数据")
    print("-" * 40)
    
    stocks = [
        ('000001', 'sh', '上证指数'),
        ('399001', 'sz', '深证成指'),
        ('399006', 'cyb', '创业板指')
    ]
    
    for symbol, market, name in stocks:
        data = get_stock_data(symbol, market, '2024-12-01', '2024-12-31')
        if data is not None and not data.empty:
            # 安全地获取收盘价
            if '收盘' in data.columns:
                latest_price = data.iloc[-1]['收盘']
                print(f"{name} ({symbol}): 最新收盘价 {latest_price}")
            else:
                print(f"{name} ({symbol}): 数据获取成功，但无收盘价列")
        else:
            print(f"{name} ({symbol}): 获取数据失败")


def test_different_parameters():
    """测试不同参数组合"""
    
    print("\n" + "=" * 60)
    print("测试不同参数组合")
    print("=" * 60)
    
    # 测试不同的复权类型
    print("\n测试不同复权类型:")
    symbol = '000001'
    market = 'sh'
    start_date = '2024-12-01'
    end_date = '2024-12-31'
    
    for adjust in ['qfq', 'hfq', '']:
        data = get_stock_data(symbol, market, start_date, end_date, adjust=adjust)
        if data is not None and not data.empty:
            print(f"复权类型 {adjust}: 数据形状 {data.shape}")
        else:
            print(f"复权类型 {adjust}: 获取失败")
    
    # 测试不同的时间周期
    print("\n测试不同时间周期:")
    for period in ['daily', 'weekly', 'monthly']:
        data = get_stock_data(symbol, market, start_date, end_date, period=period)
        if data is not None and not data.empty:
            print(f"周期 {period}: 数据形状 {data.shape}")
        else:
            print(f"周期 {period}: 获取失败")


if __name__ == "__main__":
    # 运行主示例
    main()
    
    # 运行参数测试
    test_different_parameters()
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)
