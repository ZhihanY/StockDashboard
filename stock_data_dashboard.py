import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from api import StockDataAPI, get_stock_data, get_market_list, get_screener_data


#"""主函数"""
st.set_page_config(
page_title="男大自用股票数据获取系统",
page_icon="",
layout="wide"
)

st.title(" 股票数据获取Dashboard")
st.markdown("支持上证、深证、创业板、美股数据获取")

# 创建API实例
api = StockDataAPI()

# 侧边栏参数设置
st.sidebar.header("参数设置")

# 市场选择
market = st.sidebar.selectbox(
"选择市场",
options=['sh', 'sz', 'cyb', 'us'],
format_func=lambda x: {
    'sh': '上证',
    'sz': '深证', 
    'cyb': '创业板',
    'us': '美股'
}[x]
)

# 股票代码输入
if market == 'us':
    symbol = st.sidebar.text_input("股票代码", value="AAPL", help="美股代码，如：AAPL, MSFT, GOOGL")
else:
    symbol = st.sidebar.text_input("股票代码", value="000001", help="A股代码，如：000001, 000002, 300001")

# 日期范围选择
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
    "开始日期",
    value=datetime.now() - timedelta(days=365),
    max_value=datetime.now()
)
with col2:
    end_date = st.date_input(
    "结束日期",
    value=datetime.now(),
    max_value=datetime.now()
)

# 数据周期选择
period = st.sidebar.selectbox(
    "数据周期",
    options=['daily', 'weekly', 'monthly'],
    format_func=lambda x: {
        'daily': '日线',
        'weekly': '周线',
        'monthly': '月线'
    }[x]
)

# 复权类型选择
adjust = st.sidebar.selectbox(
    "复权类型",
    options=['qfq', 'hfq', ''],
    format_func=lambda x: {
        'qfq': '前复权',
        'hfq': '后复权',
        '': '不复权'
    }[x]
)

# 主内容区域
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📊 股票数据", "📋 市场列表", "📈 图表分析", "🏦 基金数据", "⭐ 自选", "🔍 股票筛选器", "ℹ️ 使用说明"])

with tab1:
    st.header("股票数据")

    if st.button("获取数据", type="primary"):
        with st.spinner("正在获取数据..."):
            # 转换日期格式
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # 获取数据
            data = get_stock_data(
                symbol=symbol,
                market=market,
                start_date=start_date_str,
                end_date=end_date_str,
                period=period,
                adjust=adjust
            )
            
            if data is not None and not data.empty:
                st.success(f"成功获取 {len(data)} 条数据")
                
                # 显示数据统计
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("数据条数", len(data))
                with col2:
                    if '收盘' in data.columns:
                        latest_price = data.iloc[-1]['收盘']
                        st.metric("最新收盘价", f"{latest_price:.2f}")
                with col3:
                    if '涨跌幅' in data.columns:
                        latest_change = data.iloc[-1]['涨跌幅']
                        st.metric("最新涨跌幅", f"{latest_change:.2f}%")
                with col4:
                    if '成交量' in data.columns:
                        avg_volume = data['成交量'].mean()
                        st.metric("平均成交量", f"{avg_volume:,.0f}")
                
                # 显示数据表格
                st.subheader("数据表格")
                st.dataframe(data, use_container_width=True)
                
                # 保存数据到session state
                st.session_state['stock_data'] = data
                st.session_state['symbol'] = symbol
                st.session_state['market'] = market
                
            else:
                st.error("获取数据失败，请检查股票代码和市场类型")

with tab2:
    st.header("市场股票列表")

    if st.button("获取市场列表", type="primary"):
        with st.spinner("正在获取市场列表..."):
            market_list = get_market_list(market)
            
            if market_list is not None and not market_list.empty:
                st.success(f"成功获取 {len(market_list)} 只股票")
                
                # 显示列表
                st.dataframe(market_list, use_container_width=True)
                
                # 搜索功能
                st.subheader("搜索股票")
                search_term = st.text_input("输入股票代码或名称进行搜索")
                
                if search_term:
                    filtered_list = market_list[
                        (market_list['代码'].str.contains(search_term, na=False)) |
                        (market_list['名称'].str.contains(search_term, na=False))
                    ]
                    st.dataframe(filtered_list, use_container_width=True)
            else:
                st.error("获取市场列表失败")

with tab3:
    st.header("图表分析")

    if 'stock_data' in st.session_state and st.session_state['stock_data'] is not None:
        data = st.session_state['stock_data']
        
        # 价格走势图
        st.subheader("价格走势图")
        
        fig = go.Figure()
        
        # 添加K线图
        if all(col in data.columns for col in ['开盘', '最高', '最低', '收盘']):
            fig.add_trace(go.Candlestick(
                x=data['日期'],
                open=data['开盘'],
                high=data['最高'],
                low=data['最低'],
                close=data['收盘'],
                name="K线"
            ))
        else:
            # 如果没有K线数据，绘制收盘价线图
            fig.add_trace(go.Scatter(
                x=data['日期'],
                y=data['收盘'] if '收盘' in data.columns else data.iloc[:, 1],
                mode='lines',
                name="收盘价"
            ))
        
        fig.update_layout(
            title=f"{st.session_state['symbol']} 价格走势",
            xaxis_title="日期",
            yaxis_title="价格",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 成交量图
        if '成交量' in data.columns:
            st.subheader("成交量图")
            
            fig_volume = px.bar(
                data, 
                x='日期', 
                y='成交量',
                title=f"{st.session_state['symbol']} 成交量"
            )
            fig_volume.update_layout(height=400)
            st.plotly_chart(fig_volume, use_container_width=True)
        
        # 涨跌幅分布
        if '涨跌幅' in data.columns:
            st.subheader("涨跌幅分布")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_hist = px.histogram(
                    data, 
                    x='涨跌幅',
                    title="涨跌幅分布直方图",
                    nbins=30
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # 涨跌统计
                positive_days = len(data[data['涨跌幅'] > 0])
                negative_days = len(data[data['涨跌幅'] < 0])
                flat_days = len(data[data['涨跌幅'] == 0])
                
                fig_pie = px.pie(
                    values=[positive_days, negative_days, flat_days],
                    names=['上涨', '下跌', '平盘'],
                    title="涨跌天数统计"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

    else:
        st.info("请先在'股票数据'标签页获取数据")

with tab4:
    st.header("基金模块")
    st.markdown("获取开放式基金净值走势，并进行可视化")

    fund_code = st.text_input("基金代码", value="110022", help="如：110022、161725 等")
    indicator = st.selectbox(
        "指标",
        options=["单位净值走势", "累计净值走势"],
        index=0
    )
    benchmark_name = st.selectbox(
        "基准指数",
        options=["不选择", "上证50", "沪深300", "中证500", "中证1000", "创业板指"],
        index=1
    )

    fcol1, fcol2 = st.columns(2)
    with fcol1:
        fund_start_date = st.date_input(
        "开始日期(基金)",
        value=datetime.now() - timedelta(days=365),
        max_value=datetime.now()
        )
    with fcol2:
        fund_end_date = st.date_input(
        "结束日期(基金)",
        value=datetime.now(),
        max_value=datetime.now()
        )

    if st.button("获取基金净值"):
        with st.spinner("正在获取基金净值..."):
            try:
                fund_df = api.get_fund_nav(
                    fund_code,
                    start_date=fund_start_date.strftime('%Y-%m-%d'),
                    end_date=fund_end_date.strftime('%Y-%m-%d'),
                    indicator=indicator
                )
                if fund_df is not None and not fund_df.empty:
                    st.success(f"成功获取 {len(fund_df)} 条净值数据")
                    st.dataframe(fund_df, use_container_width=True)

                    value_col = None
                    for cand in ["单位净值", "累计净值", "净值", "nav"]:
                        if cand in fund_df.columns:
                            value_col = cand
                            break
                    if value_col is not None and '日期' in fund_df.columns:
                        # 单独基金曲线
                        fig_nav = px.line(fund_df, x='日期', y=value_col, title=f"基金 {fund_code} {value_col} 走势")
                        st.plotly_chart(fig_nav, use_container_width=True)

                        # 基准对比（归一化到起始=100）
                        if benchmark_name != "不选择":
                            bench_df = api.get_index_history_by_name(
                                name=benchmark_name,
                                start_date=fund_start_date.strftime('%Y-%m-%d'),
                                end_date=fund_end_date.strftime('%Y-%m-%d')
                            )
                            if bench_df is not None and not bench_df.empty and '日期' in bench_df.columns and '收盘' in bench_df.columns:
                                # 对齐日期
                                f = fund_df[['日期', value_col]].dropna().copy()
                                b = bench_df[['日期', '收盘']].dropna().copy()
                                merged = pd.merge(f, b, on='日期', how='inner')
                                if not merged.empty:
                                    merged.sort_values('日期', inplace=True)
                                    merged['基金_归一化'] = merged[value_col] / merged[value_col].iloc[0] * 100.0
                                    merged['基准_归一化'] = merged['收盘'] / merged['收盘'].iloc[0] * 100.0

                                    fig_cmp = go.Figure()
                                    fig_cmp.add_trace(go.Scatter(x=merged['日期'], y=merged['基金_归一化'], mode='lines', name=f"基金 {fund_code}"))
                                    fig_cmp.add_trace(go.Scatter(x=merged['日期'], y=merged['基准_归一化'], mode='lines', name=f"基准 {benchmark_name}"))
                                    fig_cmp.update_layout(title=f"基金与基准对比（归一化=100）", xaxis_title="日期", yaxis_title="指数")
                                    st.plotly_chart(fig_cmp, use_container_width=True)
                            else:
                                st.info("未获取到有效的基准指数数据用于对比。")
                    else:
                        st.info("未找到净值列或日期列用于绘图，请查看表格列名。")
                else:
                    st.error("未获取到基金数据，请检查基金代码或时间范围")
            except Exception as e:
                st.error(f"获取失败: {e}")

with tab5:
    selection = ['022364','516780','159748','159937','159819']
    st.header("自选策略模块")
    st.markdown("将自选基金按设定仓位聚合为组合净值，并与基准对比")

    codes_str = st.text_input("自选基金代码（逗号分隔）", value=",".join(selection))
    mode = st.radio("分配方式", options=["按权重(%)", "按份数"], index=0, horizontal=True)
    cash_weight = st.number_input("现金仓位(%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
    bench_name = st.selectbox("基准指数", options=["不选择", "上证50", "沪深300", "中证500", "中证1000", "创业板指"], index=2)

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        p_start = st.date_input("开始日期(组合)", value=datetime.now() - timedelta(days=365), max_value=datetime.now())
    with pcol2:
        p_end = st.date_input("结束日期(组合)", value=datetime.now(), max_value=datetime.now())

    codes = [c.strip() for c in codes_str.split(',') if c.strip()]
    allocations = {}
    if mode == "按权重(%)":
        st.subheader("基金权重设置(%)")
        for c in codes:
            allocations[c] = st.number_input(f"{c} 权重(%)", min_value=0.0, max_value=100.0, value=round((100.0-cash_weight)/max(len(codes),1), 2), step=1.0, key=f"w_{c}")
    else:
        st.subheader("基金份数设置")
        for c in codes:
            allocations[c] = st.number_input(f"{c} 份数", min_value=0.0, value=1.0, step=1.0, key=f"u_{c}")

    if st.button("计算组合净值并对比"):
        with st.spinner("正在计算组合..."):
            try:
                # 获取各基金净值
                fund_series = []
                value_cols = {}
                for c in codes:
                    df = api.get_fund_nav(
                        c,
                        start_date=p_start.strftime('%Y-%m-%d'),
                        end_date=p_end.strftime('%Y-%m-%d'),
                        indicator="单位净值走势"
                    )
                    if df is None or df.empty:
                        continue
                    val_col = None
                    for cand in ["单位净值", "累计净值", "净值", "nav"]:
                        if cand in df.columns:
                            val_col = cand
                            break
                    if '日期' not in df.columns or val_col is None:
                        continue
                    s = df[['日期', val_col]].dropna().copy()
                    s.rename(columns={val_col: c}, inplace=True)
                    fund_series.append(s)
                    value_cols[c] = val_col

                if len(fund_series) == 0:
                    st.error("未获取到有效基金数据，请检查代码与时间范围")
                else:
                    # 合并为同一日期
                    from functools import reduce
                    merged = reduce(lambda left, right: pd.merge(left, right, on='日期', how='inner'), fund_series)
                    if merged.empty:
                        st.error("自选基金在所选区间内无共同交易日，无法对齐计算")
                    else:
                        merged.sort_values('日期', inplace=True)
                        # 计算组合归一化净值
                        if mode == "按权重(%)":
                            total_weight = sum(allocations.values()) + cash_weight
                            if total_weight == 0:
                                st.error("总权重为0，无法计算")
                            else:
                                weights = {c: (allocations.get(c, 0.0) / total_weight) for c in codes}
                                cash_w = cash_weight / total_weight
                                # 归一化每只基金到起点=1
                                for c in codes:
                                    merged[f"{c}_norm"] = merged[c] / merged[c].iloc[0]
                                merged['组合_归一化'] = cash_w * 1.0
                                for c in codes:
                                    merged['组合_归一化'] += weights[c] * merged[f"{c}_norm"]
                        else:
                            # 份数模式：按份数与初始总资产归一
                            base = 0.0
                            for c in codes:
                                base += allocations.get(c, 0.0) * merged[c].iloc[0]
                            base += cash_weight  # 现金作为固定面额，视为与份数无关的常量（单位基数）
                            if base == 0:
                                st.error("初始资产为0，无法计算")
                            else:
                                merged['组合_绝对'] = cash_weight
                                for c in codes:
                                    merged['组合_绝对'] += allocations.get(c, 0.0) * merged[c]
                                merged['组合_归一化'] = merged['组合_绝对'] / merged['组合_绝对'].iloc[0]

                        # 对比基准
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(x=merged['日期'], y=merged['组合_归一化']*100.0, mode='lines', name='组合(归一=100)'))

                        if bench_name != "不选择":
                            bench_df = api.get_index_history_by_name(bench_name, p_start.strftime('%Y-%m-%d'), p_end.strftime('%Y-%m-%d'))
                            if bench_df is not None and not bench_df.empty:
                                b = pd.merge(merged[['日期']], bench_df[['日期','收盘']], on='日期', how='inner')
                                if not b.empty:
                                    b.sort_values('日期', inplace=True)
                                    b['基准_归一化'] = b['收盘'] / b['收盘'].iloc[0] * 100.0
                                    fig.add_trace(go.Scatter(x=b['日期'], y=b['基准_归一化'], mode='lines', name=f'基准 {bench_name}'))

                        fig.update_layout(title="组合与基准对比（归一化=100）", xaxis_title="日期", yaxis_title="指数")
                        st.plotly_chart(fig, use_container_width=True)

                        st.subheader("组合对齐数据（示例前5行）")
                        st.dataframe(merged.head(), use_container_width=True)
            except Exception as e:
                st.error(f"计算失败: {e}")

with tab6:
    st.header("股票筛选器")
    st.markdown("根据您设定的条件筛选股票")

    # 筛选条件输入
    st.subheader("筛选条件")
    
    screener_market = st.selectbox(
        "选择市场进行筛选",
        options=['sh', 'sz', 'cyb', 'us'],
        format_func=lambda x: {
            'sh': '上证',
            'sz': '深证', 
            'cyb': '创业板',
            'us': '美股'
        }[x],
        key='screener_market'
    )

    # 时间量级选择
    screener_period = st.selectbox(
        "时间量级 (目前仅影响数据获取，筛选基于实时数据)",
        options=['daily', 'weekly', 'monthly'],
        format_func=lambda x: {
            'daily': '日线',
            'weekly': '周线',
            'monthly': '月线'
        }[x],
        key='screener_period'
    )

    col_price, col_change = st.columns(2)
    with col_price:
        min_price = st.number_input("当前价格 (Min)", value=0.0, step=0.1, key='min_price')
        max_price = st.number_input("当前价格 (Max)", value=10000.0, step=0.1, key='max_price')
    with col_change:
        min_change = st.number_input("涨跌幅 (%) (Min)", value=-100.0, step=0.1, key='min_change')
        max_change = st.number_input("涨跌幅 (%) (Max)", value=100.0, step=0.1, key='max_change')

    col_marketcap, col_volume = st.columns(2)
    with col_marketcap:
        min_marketcap = st.number_input("当前市值 (亿) (Min)", value=0.0, step=1.0, key='min_marketcap')
        max_marketcap = st.number_input("当前市值 (亿) (Max)", value=100000.0, step=1.0, key='max_marketcap')
    with col_volume:
        min_volume = st.number_input("交易量 (手) (Min)", value=0.0, step=1.0, key='min_volume')
        max_volume = st.number_input("交易量 (手) (Max)", value=100000000.0, step=1.0, key='max_volume')

    col_pe, col_roe = st.columns(2)
    with col_pe:
        min_pe = st.number_input("当前P/E (Min)", value=0.0, step=0.1, key='min_pe')
        max_pe = st.number_input("当前P/E (Max)", value=1000.0, step=0.1, key='max_pe')
    with col_roe:
        st.info("营收增长 (暂不支持)")
        st.info("ROE (trailing 12 month) (暂不支持)")
        # min_revenue_growth = st.number_input("营收增长 (%) (Min)", value=-100.0, step=0.1, key='min_revenue_growth')
        # max_revenue_growth = st.number_input("营收增长 (%) (Max)", value=1000.0, step=0.1, key='max_revenue_growth')
        # min_roe = st.number_input("ROE (trailing 12 month) (%) (Min)", value=-100.0, step=0.1, key='min_roe')
        # max_roe = st.number_input("ROE (trailing 12 month) (%) (Max)", value=100.0, step=0.1, key='max_roe')

    if st.button("开始筛选", type="primary", key='start_screener'):
        with st.spinner("正在获取并筛选数据..."):
            screener_data = get_screener_data(market=screener_market)
            
            if screener_data is not None and not screener_data.empty:
                filtered_data = screener_data.copy()
                
                # 应用筛选条件
                filtered_data = filtered_data[
                    (filtered_data['当前价格'] >= min_price) & 
                    (filtered_data['当前价格'] <= max_price)    
                ]
                filtered_data = filtered_data[
                    (filtered_data['涨跌幅'] >= min_change) & 
                    (filtered_data['涨跌幅'] <= max_change)
                ]
                # 市值单位转换：akshare返回的总市值是亿元，这里用户输入也是亿
                filtered_data = filtered_data[
                    (filtered_data['当前市值'] >= min_marketcap) & 
                    (filtered_data['当前市值'] <= max_marketcap)
                ]
                filtered_data = filtered_data[
                    (filtered_data['交易量'] >= min_volume) & 
                    (filtered_data['交易量'] <= max_volume)
                ]
                filtered_data = filtered_data[
                    (filtered_data['当前P/E'] >= min_pe) & 
                    (filtered_data['当前P/E'] <= max_pe)
                ]
                
                st.success(f"筛选完成，找到 {len(filtered_data)} 只股票")
                st.dataframe(filtered_data, use_container_width=True)
            else:
                st.error("获取筛选数据失败，请检查市场类型或稍后再试")

with tab7:
    st.markdown("""
    ### 📖 功能说明

    - 股票数据获取（上证、深证、创业板、美股）
    - 市场列表与搜索
    - 图表分析（K线、成交量、涨跌幅分布）
    - 基金净值查询与可视化

    ### 🔧 参数说明（股票）
    - 市场：`sh`、`sz`、`cyb`、`us`
    - 周期：`daily`、`weekly`、`monthly`
    - 复权：`qfq`、`hfq`、``

    ### 🔧 参数说明（基金）
    - 基金代码：如 `110022`、`161725` 等
    - 指标：`单位净值走势` 或 `累计净值走势`

    ### ⚠️ 注意事项
    1. 数据获取可能需要一些时间，请耐心等待
    2. 部分标的可能因停牌等原因无法获取数据
    3. 美股数据可能因时差问题有延迟
    4. 建议使用较短的日期范围以提高获取速度
    """)


#---
