import pandas as pd
from datetime import datetime, timedelta
from api import StockDataAPI, get_market_list, get_stock_data
import time
import os

TEMP_CSV_PATH = "us_stock_data_temp.csv"
FINAL_CSV_PATH = "us_stock_data_2023_2025.csv"

def fetch_and_save_us_stock_data():
    """
    获取所有美股股票2023-2025年的日级数据，并保存到本地CSV文件。
    支持断点续传。
    """
    api = StockDataAPI()
    
    st.info("正在获取美股市场列表...")
    us_market_list = get_market_list(market='us')
    
    if us_market_list is None or us_market_list.empty:
        st.error("获取美股市场列表失败。")
        return

    st.success(f"成功获取 {len(us_market_list)} 只美股。")
    
    processed_symbols = set()
    if os.path.exists(TEMP_CSV_PATH):
        st.info(f"检测到临时文件 {TEMP_CSV_PATH}，尝试从中断处恢复...")
        try:
            temp_df = pd.read_csv(TEMP_CSV_PATH, encoding='utf-8-sig')
            processed_symbols = set(temp_df['股票代码'].unique())
            st.success(f"已从临时文件加载 {len(processed_symbols)} 只股票的数据。")
        except Exception as e:
            st.warning(f"加载临时文件失败: {e}。将从头开始获取数据。")
            processed_symbols = set() # 重置已处理列表

    all_stock_data_new = [] # 用于存储本次运行新获取的数据
    
    # 定义日期范围
    years = [2025, 2024, 2023] # 从2025年开始取，如用户要求
    
    for index, row in us_market_list.iterrows():
        symbol = row['代码']
        stock_name = row['名称']

        if symbol in processed_symbols:
            st.write(f"跳过已处理的股票: {stock_name} ({symbol})")
            continue

        st.write(f"正在获取 {stock_name} ({symbol}) 的数据...")
        
        stock_data_for_symbol = []
        for year in years:
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            # 对于当前年份，结束日期不能超过今天
            if year == datetime.now().year:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            try:
                data = get_stock_data(
                    symbol=symbol,
                    market='us',
                    start_date=start_date,
                    end_date=end_date,
                    period='daily',
                    adjust='' # 不复权，或者根据需求选择qfq/hfq
                )
                if data is not None and not data.empty:
                    stock_data_for_symbol.append(data)
                    # 打印获取的数据日期及数据量
                    first_date = data['日期'].min().strftime('%Y-%m-%d')
                    last_date = data['日期'].max().strftime('%Y-%m-%d')
                    st.write(f"  - 获取 {year} 年数据成功: 日期从 {first_date} 到 {last_date}, 共 {len(data)} 条数据。")
                else:
                    st.write(f"  - 获取 {year} 年数据失败或为空。")
            except Exception as e:
                st.error(f"获取 {symbol} ({year} 年) 数据时发生错误: {e}")
            
            time.sleep(0.5) # 每次请求后暂停0.5秒，以应对可能的接口限流

        if stock_data_for_symbol:
            combined_data = pd.concat(stock_data_for_symbol).drop_duplicates(subset=['日期']).sort_values('日期').reset_index(drop=True)
            combined_data['股票代码'] = symbol
            combined_data['股票名称'] = stock_name
            all_stock_data_new.append(combined_data)
            st.success(f"成功获取并合并 {stock_name} ({symbol}) 的所有数据。")
            
            # 每次成功获取一只股票的数据后，保存到临时文件
            if not os.path.exists(TEMP_CSV_PATH):
                combined_data.to_csv(TEMP_CSV_PATH, index=False, encoding='utf-8-sig')
            else:
                combined_data.to_csv(TEMP_CSV_PATH, mode='a', header=False, index=False, encoding='utf-8-sig')
            st.info(f"数据已保存到临时文件: {TEMP_CSV_PATH}")
        else:
            st.warning(f"未能获取 {stock_name} ({symbol}) 的任何数据。")

    # 合并所有数据（包括从临时文件加载的和新获取的）
    final_df = None
    if os.path.exists(TEMP_CSV_PATH):
        try:
            final_df = pd.read_csv(TEMP_CSV_PATH, encoding='utf-8-sig')
            if all_stock_data_new:
                newly_fetched_df = pd.concat(all_stock_data_new)
                final_df = pd.concat([final_df, newly_fetched_df]).drop_duplicates(subset=['股票代码', '日期']).sort_values(['股票代码', '日期']).reset_index(drop=True)
            st.success(f"最终数据包含 {len(final_df['股票代码'].unique())} 只股票，共 {len(final_df)} 条记录。")
        except Exception as e:
            st.error(f"合并临时文件和新数据时发生错误: {e}")
            if all_stock_data_new:
                final_df = pd.concat(all_stock_data_new).drop_duplicates(subset=['股票代码', '日期']).sort_values(['股票代码', '日期']).reset_index(drop=True)
            else:
                final_df = None
    elif all_stock_data_new:
        final_df = pd.concat(all_stock_data_new).drop_duplicates(subset=['股票代码', '日期']).sort_values(['股票代码', '日期']).reset_index(drop=True)

    if final_df is not None and not final_df.empty:
        final_df.to_csv(FINAL_CSV_PATH, index=False, encoding='utf-8-sig')
        st.success(f"所有美股数据已成功保存到最终文件: {FINAL_CSV_PATH}")
        st.dataframe(final_df.head())
        # 清理临时文件
        if os.path.exists(TEMP_CSV_PATH):
            os.remove(TEMP_CSV_PATH)
            st.info(f"临时文件 {TEMP_CSV_PATH} 已清理。")
    else:
        st.error("未能获取任何美股数据。")

if __name__ == "__main__":
    import streamlit as st
    st.set_page_config(page_title="美股数据获取工具", layout="wide")
    st.title("美股数据获取与保存")
    st.markdown("此工具将获取所有美股2023-2025年的日级数据，并保存为CSV文件。支持断点续传。")

    if st.button("开始获取美股数据", type="primary"):
        fetch_and_save_us_stock_data()
