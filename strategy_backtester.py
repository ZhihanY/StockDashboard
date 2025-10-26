import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit as st # Streamlit is used for displaying results, so it's needed here too

def run_backtest_strategy(
    api,
    strategy_symbol,
    strategy_start_date,
    strategy_end_date,
    initial_capital,
    bb_period,
    bb_std_dev,
    macd_fast_period,
    macd_slow_period,
    macd_signal_period,
    rsi_period,
    rsi_oversold,
    rsi_overbought
):
    """
    Runs a backtesting strategy based on Bollinger Bands, MACD, and RSI.

    Args:
        api: An instance of StockDataAPI for fetching data.
        strategy_symbol (str): The stock symbol to backtest.
        strategy_start_date (datetime.date): The start date for the backtest.
        strategy_end_date (datetime.date): The end date for the backtest.
        initial_capital (float): The initial capital for the backtest.
        bb_period (int): Period for Bollinger Bands.
        bb_std_dev (float): Standard deviation for Bollinger Bands.
        macd_fast_period (int): Fast EMA period for MACD.
        macd_slow_period (int): Slow EMA period for MACD.
        macd_signal_period (int): Signal line EMA period for MACD.
        rsi_period (int): Period for RSI.
        rsi_oversold (int): Oversold threshold for RSI.
        rsi_overbought (int): Overbought threshold for RSI.

    Returns:
        tuple: A tuple containing (fig_strategy, strategy_df, buy_dates, sell_dates, final_cash, final_shares, final_portfolio_value, df_with_indicators)
               or (None, None, None, None, None, None, None, None) if an error occurs.
    """
    st.subheader("正在获取数据并运行策略...")
    
    stock_data = pd.DataFrame()
    try:
        all_us_stock_data = pd.read_csv('us2_stock_data_temp.csv', encoding='utf-8-sig')
        all_us_stock_data['日期'] = pd.to_datetime(all_us_stock_data['日期'])

        stock_data = all_us_stock_data[all_us_stock_data['股票代码'] == strategy_symbol].copy()
        
        stock_data = stock_data[
            (stock_data['日期'] >= pd.to_datetime(strategy_start_date)) &
            (stock_data['日期'] <= pd.to_datetime(strategy_end_date))
        ]
        
        if stock_data.empty:
            st.error(f"在 'us2_stock_data_temp.csv' 中未能找到 {strategy_symbol} 在指定日期范围内的历史数据。")
            return None, None, None, None, None, None, None, None
    except FileNotFoundError:
        st.error("未找到 'us2_stock_data_temp.csv' 文件。请确保文件存在。")
        return None, None, None, None, None, None, None, None
    except Exception as e:
        st.error(f"加载或处理 'us2_stock_data_temp.csv' 文件时发生错误: {e}")
        return None, None, None, None, None, None, None, None

    if stock_data.empty or 'close' not in stock_data.columns:
        st.error("未能获取到有效的股票数据或'close'列缺失。")
        return None, None, None, None, None, None, None, None

    df = stock_data.copy()
    df.set_index('日期', inplace=True)
    df.sort_index(inplace=True)

    # Calculate Bollinger Bands
    df = api._calculate_bollinger_bands(df, bb_period, bb_std_dev)
    df[f'SMA_{bb_period}_Middle_Band_SMA_5'] = df[f'SMA_{bb_period}'].rolling(window=5).mean() # Corrected to use SMA_bb_period

    # Calculate MACD
    df[f'EMA_Fast_{macd_fast_period}'] = df['close'].ewm(span=macd_fast_period, adjust=False).mean()
    df[f'EMA_Slow_{macd_slow_period}'] = df['close'].ewm(span=macd_slow_period, adjust=False).mean()
    df['MACD'] = df[f'EMA_Fast_{macd_fast_period}'] - df[f'EMA_Slow_{macd_slow_period}']
    df['Signal'] = df['MACD'].ewm(span=macd_signal_period, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']

    # Calculate RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Strategy Simulation
    cash = initial_capital
    shares = 0
    portfolio_value = []
    buy_dates = []
    sell_dates = []

    first_tradable_index = df['close'].first_valid_index()
    if first_tradable_index is not None:
        first_trade_date = df.loc[first_tradable_index].name
        first_trade_price = df.loc[first_tradable_index]['close']
        
        if cash > 0 and first_trade_price > 0:
            initial_shares_to_buy = cash // first_trade_price
            if initial_shares_to_buy > 0:
                shares += initial_shares_to_buy
                cash -= initial_shares_to_buy * first_trade_price
                buy_dates.append(first_trade_date)

    start_loop_index = df.index.get_loc(first_tradable_index) if first_tradable_index is not None else 0
    first_valid_indicator_index = df[['RSI', 'MACD', 'Signal', f'UpperBB_{bb_period}_{bb_std_dev}', f'LowerBB_{bb_period}_{bb_std_dev}', f'SMA_{bb_period}', f'SMA_{bb_period}_Middle_Band_SMA_5']].dropna().index.min()
    if first_valid_indicator_index is not None:
        start_loop_index = max(start_loop_index, df.index.get_loc(first_valid_indicator_index))
    
    for i in range(start_loop_index):
        portfolio_value.append(cash + shares * df['close'].iloc[i])

    for i in range(start_loop_index, len(df)):
        current_date = df.index[i]
        prev_date = df.index[i-1]

        if (pd.isna(df['RSI'].iloc[i]) or pd.isna(df['MACD'].iloc[i]) or pd.isna(df['Signal'].iloc[i]) or
            pd.isna(df[f'UpperBB_{bb_period}_{bb_std_dev}'].iloc[i]) or pd.isna(df[f'LowerBB_{bb_period}_{bb_std_dev}'].iloc[i]) or
            pd.isna(df[f'SMA_{bb_period}'].iloc[i]) or pd.isna(df[f'SMA_{bb_period}_Middle_Band_SMA_5'].iloc[i])):
            portfolio_value.append(cash + shares * df['close'].iloc[i])
            continue

        current_close = df['close'].iloc[i]
        prev_close = df['close'].iloc[i-1]
        current_rsi = df['RSI'].iloc[i]
        prev_rsi = df['RSI'].iloc[i-1]
        current_macd = df['MACD'].iloc[i]
        prev_macd = df['MACD'].iloc[i-1]
        current_signal = df['Signal'].iloc[i]
        prev_signal = df['Signal'].iloc[i-1]
        current_histogram = df['Histogram'].iloc[i]
        prev_histogram = df['Histogram'].iloc[i-1]
        
        upper_bb = df[f'UpperBB_{bb_period}_{bb_std_dev}'].iloc[i]
        lower_bb = df[f'LowerBB_{bb_period}_{bb_std_dev}'].iloc[i]
        middle_bb = df[f'SMA_{bb_period}'].iloc[i]
        middle_bb_sma_5 = df[f'SMA_{bb_period}_Middle_Band_SMA_5'].iloc[i]
        prev_middle_bb_sma_5 = df[f'SMA_{bb_period}_Middle_Band_SMA_5'].iloc[i-1]

        # Buy conditions
        boll_buy_condition = (prev_close < lower_bb and current_close >= lower_bb and current_close < middle_bb and
                              middle_bb > prev_middle_bb_sma_5)

        macd_buy_condition = (current_macd > current_signal and prev_macd <= prev_signal and
                              current_histogram > 0 and prev_histogram <= 0)

        rsi_buy_condition = (prev_rsi < rsi_oversold and current_rsi >= rsi_oversold and current_rsi <= 50)

        if (boll_buy_condition and macd_buy_condition and rsi_buy_condition and cash > 0):
            buy_price = current_close
            shares_to_buy = cash // buy_price
            if shares_to_buy > 0:
                shares += shares_to_buy
                cash -= shares_to_buy * buy_price
                buy_dates.append(current_date)

        # Sell conditions
        boll_sell_condition = (current_close > upper_bb)

        macd_sell_condition = (current_macd < current_signal and prev_macd >= prev_signal and
                               current_histogram < 0 and prev_histogram >= 0)

        rsi_sell_condition = (current_rsi >= rsi_overbought)

        if (boll_sell_condition and macd_sell_condition and rsi_sell_condition and shares > 0):
            sell_price = current_close
            cash += shares * sell_price
            shares = 0
            sell_dates.append(current_date)
        
        portfolio_value.append(cash + shares * df['close'].iloc[i])
    
    strategy_df = pd.DataFrame({
        '日期': df.index,
        '策略资金': portfolio_value
    })
    strategy_df.set_index('日期', inplace=True)

    # Get benchmark data (SPY, QQQ)
    benchmarks = ['SPY', 'QQQ']
    benchmark_dfs = {}
    for bench_symbol in benchmarks:
        bench_data = api.get_stock_data(
            symbol=bench_symbol,
            market='us', # Assuming 'us' for benchmarks
            start_date=strategy_start_date.strftime('%Y-%m-%d'),
            end_date=strategy_end_date.strftime('%Y-%m-%d'),
            period='daily',
            adjust='qfq'
        )
        if bench_data is not None and not bench_data.empty and 'close' in bench_data.columns:
            bench_data.set_index('日期', inplace=True)
            bench_data.sort_index(inplace=True)
            aligned_bench_data = pd.merge(strategy_df.index.to_frame(), bench_data[['close']], left_index=True, right_index=True, how='inner')
            if not aligned_bench_data.empty:
                initial_bench_price = aligned_bench_data['close'].iloc[0]
                aligned_bench_data['绝对资金'] = (aligned_bench_data['close'] / initial_bench_price) * initial_capital
                benchmark_dfs[bench_symbol] = aligned_bench_data['绝对资金']
        else:
            st.warning(f"未能获取基准 {bench_symbol} 的数据。")

    # Plotting
    fig_strategy = go.Figure()
    fig_strategy.add_trace(go.Scatter(x=strategy_df.index, y=strategy_df['策略资金'], mode='lines', name=f'{strategy_symbol} 策略 ({initial_capital:.0f} USD)'))

    for bench_symbol, bench_series in benchmark_dfs.items():
        fig_strategy.add_trace(go.Scatter(x=bench_series.index, y=bench_series, mode='lines', name=f'基准 {bench_symbol}'))

    fig_strategy.update_layout(
        title=f"{strategy_symbol} 策略回测 vs 基准 ({strategy_start_date.strftime('%Y-%m-%d')} - {strategy_end_date.strftime('%Y-%m-%d')})",
        xaxis_title="日期",
        yaxis_title="绝对资金 (USD)",
        hovermode="x unified",
        height=600
    )

    final_portfolio_value = cash + shares * df['close'].iloc[-1] if not df.empty else cash

    return fig_strategy, strategy_df, buy_dates, sell_dates, cash, shares, final_portfolio_value, df
