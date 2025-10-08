import pandas as pd
from datetime import datetime, timedelta
from api import StockDataAPI, get_market_list, get_stock_data
import time
import os
import streamlit as st
import traceback
import random 


TEMP_CSV_PATH = "us2_stock_data_temp.csv"
# FINAL_CSV_PATH will be dynamically generated

def fetch_and_save_us_stock_data(user_start_date: datetime, user_end_date: datetime):
    """
    获取所有美股股票指定日期范围内的日级数据，并保存到本地CSV文件。
    支持断点续传。
    """
    api = StockDataAPI()
    
    st.info("正在获取美股市场列表...")
    us_market_list = pd.read_csv('ticker_list.csv') #get_market_list(market='us')
    
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
    
    for index, row in us_market_list.iterrows():
        symbol = row['symbol']
        stock_name = row['name']

        if symbol in processed_symbols:
            continue

        st.info(f"正在获取 {stock_name} ({symbol}) 的数据...")
        
        start_date_str = user_start_date.strftime('%Y-%m-%d')
        end_date_str = user_end_date.strftime('%Y-%m-%d')
        
        try:
            data = get_stock_data(
                symbol=symbol,
                market='us2',
                start_date=start_date_str,
                end_date=end_date_str,
                period='daily',
                adjust='' # 不复权，或者根据需求选择qfq/hfq
            )
            # if data is not None and not data.empty:
            #     combined_data = data.drop_duplicates(subset=['日期']).sort_values('日期').reset_index(drop=True)
            #     combined_data['股票代码'] = symbol
            #     combined_data['股票名称'] = stock_name
            #     all_stock_data_new.append(combined_data)

            #     first_date = combined_data['日期'].min().strftime('%Y-%m-%d')
            #     last_date = combined_data['日期'].max().strftime('%Y-%m-%d')
            #     st.write(f"  - 获取 {stock_name} ({symbol}) 数据成功: 日期从 {first_date} 到 {last_date}, 共 {len(combined_data)} 条数据。")
                
            #     # 每次成功获取一只股票的数据后，保存到临时文件
            #     if not os.path.exists(TEMP_CSV_PATH):
            #         combined_data.to_csv(TEMP_CSV_PATH, index=False, encoding='utf-8-sig')
            #     else:
            #         combined_data.to_csv(TEMP_CSV_PATH, mode='a', header=False, index=False, encoding='utf-8-sig')
            #     st.info(f"数据已保存到临时文件: {TEMP_CSV_PATH}")
            # else:
            #     st.write(f"  - 获取 {stock_name} ({symbol}) 数据失败或为空。")
            if data is not None and not data.empty:
                #combined_data = data.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
                combined_data = data.copy()
                combined_data.rename(columns={'date': '日期'}, inplace=True)
                combined_data['股票代码'] = symbol
                combined_data['股票名称'] = stock_name
                all_stock_data_new.append(combined_data)

                first_date = combined_data['日期'].min().strftime('%Y-%m-%d')
                last_date = combined_data['日期'].max().strftime('%Y-%m-%d')
                st.write(f"  - 获取 {stock_name} ({symbol}) 数据成功: 日期从 {first_date} 到 {last_date}, 共 {len(combined_data)} 条数据。")
                
                # 每次成功获取一只股票的数据后，保存到临时文件
                if not os.path.exists(TEMP_CSV_PATH):
                    combined_data.to_csv(TEMP_CSV_PATH, index=False, encoding='utf-8-sig')
                else:
                    combined_data.to_csv(TEMP_CSV_PATH, mode='a', header=False, index=False, encoding='utf-8-sig')
                st.info(f"数据已保存到临时文件: {TEMP_CSV_PATH}")
            else:
                st.write(f"  - 获取 {stock_name} ({symbol}) 数据失败或为空。")

        except Exception as e:
            st.error(f"获取 {symbol} 数据时发生错误: {type(e).__name__} - {e}\nTraceback:\n{traceback.format_exc()}")
        
        time.sleep(random.randint(1, 5)) # 每次请求后暂停0.5秒，以应对可能的接口限流

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
        final_df_path = f"us_stock_data_{user_start_date.strftime('%Y%m%d')}_{user_end_date.strftime('%Y%m%d')}.csv"
        final_df.to_csv(final_df_path, index=False, encoding='utf-8-sig')
        st.success(f"所有美股数据已成功保存到最终文件: {final_df_path}")
        st.dataframe(final_df.head())
        # 清理临时文件
        if os.path.exists(TEMP_CSV_PATH):
            os.remove(TEMP_CSV_PATH)
            st.info(f"临时文件 {TEMP_CSV_PATH} 已清理。")
    else:
        st.error("未能获取任何美股数据。")

if __name__ == "__main__":
    st.set_page_config(page_title="美股数据获取工具", layout="wide")
    st.title("美股数据获取与保存")
    st.markdown("此工具将获取所有美股指定日期范围内的日级数据，并保存为CSV文件。支持断点续传。")

    col1, col2 = st.columns(2)
    with col1:
        default_start_date = datetime.now() - timedelta(days=365 * 3) # 默认3年前
        start_date_input = st.date_input(
            "开始日期",
            value=default_start_date,
            max_value=datetime.now()
        )
    with col2:
        end_date_input = st.date_input(
            "结束日期",
            value=datetime.now(),
            max_value=datetime.now()
        )

    if st.button("开始获取美股数据", type="primary"):
        # Convert date.date objects to datetime.datetime for consistent comparison
        start_datetime_input = datetime.combine(start_date_input, datetime.min.time())
        end_datetime_input = datetime.combine(end_date_input, datetime.min.time())

        if start_datetime_input > end_datetime_input:
            st.error("开始日期不能晚于结束日期。")
        else:
            fetch_and_save_us_stock_data(start_datetime_input, end_datetime_input)
