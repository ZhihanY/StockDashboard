import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from api import StockDataAPI, get_stock_data, get_market_list, get_screener_data, calculate_bollinger_bands


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

# Alpha Vantage API Key (从api.py中移过来，或者从环境变量加载)

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_cached_stock_data(symbol, market, start_date, end_date, period, adjust):
    return api.get_stock_data(symbol, market, start_date, end_date, period, adjust)

# 基金名称映射（缓存到 session_state）
def get_fund_name_map() -> dict:
    if 'fund_name_map' in st.session_state:
        return st.session_state['fund_name_map']
    name_map = {}
    try:
        df = ak.fund_name_em()
        if df is not None and not df.empty:
            code_col = '基金代码' if '基金代码' in df.columns else ('代码' if '代码' in df.columns else None)
            name_col = '基金简称' if '基金简称' in df.columns else ('名称' if '名称' in df.columns else None)
            if code_col and name_col:
                for _, row in df[[code_col, name_col]].dropna().iterrows():
                    name_map[str(row[code_col]).strip()] = str(row[name_col]).strip()
    except Exception:
        pass
    if not name_map:
        try:
            df2 = ak.fund_open_fund_daily_em()
            if df2 is not None and not df2.empty and {'代码','名称'}.issubset(df2.columns):
                for _, row in df2[['代码','名称']].dropna().iterrows():
                    name_map[str(row['代码']).strip()] = str(row['名称']).strip()
        except Exception:
            pass
    st.session_state['fund_name_map'] = name_map
    return name_map

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📊 股票数据", "📋 市场列表", "📈 图表分析", "🏦 基金数据", "⭐ 自选策略", "🔍 股票筛选器", "ℹ️ 使用说明", "🚀 策略回测"])

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
        with st.spinner("正在计算组合..."):
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
    st.header("策略效果模拟")
    st.markdown("在自选中选择基金或美股，按设定仓位聚合并对比")

    entity_type = st.radio("标的类型", options=["基金", "美股"], index=0, horizontal=True)

    if entity_type == "基金":
        codes_str = st.text_input("自选基金代码（逗号分隔）", value=",".join(selection))
        mode = st.radio("分配方式", options=["按权重(%)", "按份数"], index=0, horizontal=True, key="fund_mode")
        cash_weight = st.number_input("现金仓位(%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0, key="fund_cash")
        bench_name = st.selectbox("基准指数", options=["不选择", "上证50", "沪深300", "中证500", "中证1000", "创业板指"], index=2, key="fund_bench")

        pcol1, pcol2 = st.columns(2)
        with pcol1:
            p_start = st.date_input("开始日期(组合)", value=datetime.now() - timedelta(days=3650), max_value=datetime.now(), key="fund_start")
        with pcol2:
            p_end = st.date_input("结束日期(组合)", value=datetime.now(), max_value=datetime.now(), key="fund_end")

        codes = [c.strip() for c in codes_str.split(',') if c.strip()]
        name_map = get_fund_name_map()
        allocations = {}
        if mode == "按权重(%)":
            st.subheader("基金权重设置(%)")
            for c in codes:
                label = f"{c}"
                if c in name_map:
                    label = f"{c}（{name_map[c]}）"
                allocations[c] = st.number_input(f"{label} 权重(%)", min_value=0.0, max_value=100.0, value=round((100.0-cash_weight)/max(len(codes),1), 2), step=1.0, key=f"w_{c}")
        else:
            st.subheader("基金份数设置")
            for c in codes:
                label = f"{c}"
                if c in name_map:
                    label = f"{c}（{name_map[c]}）"
                allocations[c] = st.number_input(f"{label} 份数", min_value=0.0, value=1.0, step=1.0, key=f"u_{c}")

        if st.button("计算组合净值并对比", key="btn_fund_port"):
            with st.spinner("正在计算组合..."):
                try:
                    # 获取各基金净值
                    fund_series = []
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
                        col_name = c
                        if c in name_map:
                            col_name = f"{c}（{name_map[c]}）"
                        s.rename(columns={val_col: col_name}, inplace=True)
                        fund_series.append(s)

                    if len(fund_series) == 0:
                        st.error("未获取到有效基金数据，请检查代码与时间范围")
                    else:
                        from functools import reduce
                        merged = reduce(lambda left, right: pd.merge(left, right, on='日期', how='inner'), fund_series)
                        if merged.empty:
                            st.error("自选基金在所选区间内无共同交易日，无法对齐计算")
                        else:
                            merged.sort_values('日期', inplace=True)
                            if mode == "按权重(%)":
                                total_weight = sum(allocations.values()) + cash_weight
                                if total_weight == 0:
                                    st.error("总权重为0，无法计算")
                                else:
                                    weights = {c: (allocations.get(c, 0.0) / total_weight) for c in codes}
                                    cash_w = cash_weight / total_weight
                                    for col in weights.keys():
                                        merged[f"{col}_norm"] = merged[col] / merged[col].iloc[0]
                                    merged['组合_归一化'] = cash_w * 1.0
                                    for col, w in weights.items():
                                        merged['组合_归一化'] += w * merged[f"{col}_norm"]
                            else:
                                base = 0.0
                                for c in codes:
                                    key = c
                                    if c in name_map:
                                        key = f"{c}（{name_map[c]}）"
                                    base += allocations.get(c, 0.0) * merged[key].iloc[0]
                                base += cash_weight
                                if base == 0:
                                    st.error("初始资产为0，无法计算")
                                else:
                                    merged['组合_绝对'] = cash_weight
                                    for c in codes:
                                        key = c
                                        if c in name_map:
                                            key = f"{c}（{name_map[c]}）"
                                        merged['组合_绝对'] += allocations.get(c, 0.0) * merged[key]
                                    merged['组合_归一化'] = merged['组合_绝对'] / merged['组合_绝对'].iloc[0]

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

                            #st.subheader("组合对齐数据（示例前5行）")
                            #st.dataframe(merged.head(), use_container_width=True)
                except Exception as e:
                    st.error(f"计算失败: {e}")
    else:  # 美股
        codes_str = st.text_input("自选美股代码（逗号分隔）", value="AAPL,MSFT,META", key="us_codes")
        mode = st.radio("分配方式", options=["按权重(%)", "按份数"], index=0, horizontal=True, key="us_mode")
        cash_weight = st.number_input("现金仓位(%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0, key="us_cash")
        # 美股基准：SPY / QQQ / VGT
        bench_name = st.selectbox("美股基准ETF", options=["不选择", "SPY", "QQQ", "VGT"], index=0, key="us_bench")

        pcol1, pcol2 = st.columns(2)
        with pcol1:
            p_start = st.date_input("开始日期(组合)", value=datetime.now() - timedelta(days=3650), max_value=datetime.now(), key="us_start")
        with pcol2:
            p_end = st.date_input("结束日期(组合)", value=datetime.now(), max_value=datetime.now(), key="us_end")

        codes = [c.strip() for c in codes_str.split(',') if c.strip()]
        allocations = {}
        if mode == "按权重(%)":
            st.subheader("权重设置(%)")
            for c in codes:
                allocations[c] = st.number_input(f"{c} 权重(%)", min_value=0.0, max_value=100.0, value=round((100.0-cash_weight)/max(len(codes),1), 2), step=1.0, key=f"us_w_{c}")
        else:
            st.subheader("份数设置")
            for c in codes:
                allocations[c] = st.number_input(f"{c} 份数", min_value=0.0, value=1.0, step=1.0, key=f"us_u_{c}")

        if st.button("计算组合净值并对比", key="btn_us_port"):
            with st.spinner("正在计算组合..."):
                try:
                    series = []
                    skipped = []
                    for c in codes:
                        df = api.get_stock_data(
                            symbol=c,
                            market='us',
                            start_date=p_start.strftime('%Y-%m-%d'),
                            end_date=p_end.strftime('%Y-%m-%d'),
                            period='daily',
                            adjust=''
                        )
                        if df is None or df.empty or '日期' not in df.columns or '收盘' not in df.columns:
                            skipped.append(c)
                            continue
                        s = df[['日期','收盘']].dropna().copy()
                        s.rename(columns={'收盘': c}, inplace=True)
                        series.append(s)

                    if skipped:
                        st.warning(f"以下标的未能获取到有效数据并被跳过：{', '.join(skipped)}")

                    if len(series) == 0:
                        st.error("未获取到有效美股数据，请检查代码与时间范围")
                    else:
                        from functools import reduce
                        merged = series[0] if len(series) == 1 else reduce(lambda left, right: pd.merge(left, right, on='日期', how='inner'), series)
                        if merged.empty:
                            st.error("所选美股在区间内无共同交易日，无法对齐计算")
                        else:
                            merged.sort_values('日期', inplace=True)
                            if mode == "按权重(%)":
                                total_weight = sum(allocations.values()) + cash_weight
                                if total_weight == 0:
                                    st.error("总权重为0，无法计算")
                                else:
                                    weights = {c: (allocations.get(c, 0.0) / total_weight) for c in codes}
                                    cash_w = cash_weight / total_weight
                                    for c in codes:
                                        merged[f"{c}_norm"] = merged[c] / merged[c].iloc[0]
                                    merged['组合_归一化'] = cash_w * 1.0
                                    for c in codes:
                                        merged['组合_归一化'] += weights[c] * merged[f"{c}_norm"]
                            else:
                                base = 0.0
                                for c in codes:
                                    base += allocations.get(c, 0.0) * merged[c].iloc[0]
                                base += cash_weight
                                if base == 0:
                                    st.error("初始资产为0，无法计算")
                                else:
                                    merged['组合_绝对'] = cash_weight
                                    for c in codes:
                                        merged['组合_绝对'] += allocations.get(c, 0.0) * merged[c]
                                    merged['组合_归一化'] = merged['组合_绝对'] / merged['组合_绝对'].iloc[0]

                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=merged['日期'], y=merged['组合_归一化']*100.0, mode='lines', name='组合(归一=100)'))
                            # 叠加美股基准
                            if bench_name != "不选择":
                                bdf = api.get_stock_data(
                                    symbol=bench_name,
                                    market='us',
                                    start_date=p_start.strftime('%Y-%m-%d'),
                                    end_date=p_end.strftime('%Y-%m-%d'),
                                    period='daily',
                                    adjust=''
                                )
                                if bdf is not None and not bdf.empty and '日期' in bdf.columns and '收盘' in bdf.columns:
                                    bdf = bdf[['日期','收盘']].dropna().copy()
                                    bdf.sort_values('日期', inplace=True)
                                    # 对齐日期到组合
                                    bdf = pd.merge(merged[['日期']], bdf, on='日期', how='inner')
                                    if not bdf.empty:
                                        bdf['基准_归一化'] = bdf['收盘'] / bdf['收盘'].iloc[0] * 100.0
                                        fig.add_trace(go.Scatter(x=bdf['日期'], y=bdf['基准_归一化'], mode='lines', name=f'基准 {bench_name}'))

                            fig.update_layout(title="美股组合对比（归一化=100）", xaxis_title="日期", yaxis_title="指数")
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

    st.subheader("技术指标筛选")
    use_bollinger = st.checkbox("启用布林带筛选", key='use_bollinger')
    if use_bollinger:
        col_bb_period, col_bb_std = st.columns(2)
        with col_bb_period:
            bb_period = st.number_input("布林带周期", min_value=5, value=20, step=1, key='bb_period')
        with col_bb_std:
            bb_std_dev = st.number_input("布林带标准差", min_value=1.0, value=2.0, step=0.1, key='bb_std_dev')
        st.selectbox(
            "布林带条件",
            options=["价格突破上轨", "价格跌破下轨", "价格在中轨上方", "价格在中轨下方"],
            key='bb_condition'
        )

    use_ema = st.checkbox("启用EMA筛选", key='use_ema')
    if use_ema:
        ema_period = st.selectbox(
            "EMA周期",
            options=[5, 10, 20, 50, 100, 200],
            index=2, # Default to 20
            key='ema_period'
        )
        st.selectbox(
            "EMA条件",
            options=["价格在EMA上方", "价格在EMA下方", "EMA向上", "EMA向下"],
            key='ema_condition'
        )

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

                # 应用技术指标筛选
                if st.session_state.get('use_bollinger') or st.session_state.get('use_ema'):
                    st.subheader("正在应用技术指标筛选...")
                    progress_bar = st.progress(0)
                    total_stocks = len(filtered_data)
                    stocks_to_keep = []
                    
                    # Define a lookback period for historical data needed for indicators
                    # Max period for BB is 20, for EMA is 200. Use a sufficiently large period.
                    max_indicator_period = max(st.session_state.get('bb_period', 20), st.session_state.get('ema_period', 200))
                    lookback_days = max_indicator_period * 2 # Get twice the max period to ensure enough data

                    for i, (index, row) in enumerate(filtered_data.iterrows()):
                        symbol_code = row['股票代码']
                        stock_market = screener_market # Use the selected screener market
                        
                        # Fetch historical data for the stock
                        # Need enough data points for the longest indicator period
                        hist_start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
                        hist_end_date = datetime.now().strftime('%Y-%m-%d')

                        hist_data = api.get_stock_data(
                            symbol=symbol_code,
                            market=stock_market,
                            start_date=hist_start_date,
                            end_date=hist_end_date,
                            period='daily', # Indicators usually use daily data
                            adjust='qfq' # Use front-adjusted data
                        )

                        keep_stock = True
                        if hist_data is not None and not hist_data.empty and '收盘' in hist_data.columns:
                            current_price = row['当前价格'] # Use the current price from screener_data

                            # Bollinger Bands filtering
                            if st.session_state.get('use_bollinger'):
                                bb_period_val = st.session_state.get('bb_period', 20)
                                bb_std_dev_val = st.session_state.get('bb_std_dev', 2.0)
                                bb_condition_val = st.session_state.get('bb_condition')

                                hist_data_with_bb = api._calculate_bollinger_bands(hist_data.copy(), bb_period_val, bb_std_dev_val)
                                if not hist_data_with_bb.empty and len(hist_data_with_bb) >= bb_period_val:
                                    latest_bb = hist_data_with_bb.iloc[-1]
                                    upper_bb = latest_bb[f'UpperBB_{bb_period_val}_{bb_std_dev_val}']
                                    lower_bb = latest_bb[f'LowerBB_{bb_period_val}_{bb_std_dev_val}']
                                    middle_bb = latest_bb[f'SMA_{bb_period_val}']

                                    if bb_condition_val == "价格突破上轨" and not (current_price > upper_bb):
                                        keep_stock = False
                                    elif bb_condition_val == "价格跌破下轨" and not (current_price < lower_bb):
                                        keep_stock = False
                                    elif bb_condition_val == "价格在中轨上方" and not (current_price > middle_bb):
                                        keep_stock = False
                                    elif bb_condition_val == "价格在中轨下方" and not (current_price < middle_bb):
                                        keep_stock = False
                                else:
                                    keep_stock = False # Not enough data for BB or calculation failed

                            # EMA filtering (only if still kept by BB or BB not used)
                            if keep_stock and st.session_state.get('use_ema'):
                                ema_period_val = st.session_state.get('ema_period', 20)
                                ema_condition_val = st.session_state.get('ema_condition')

                                hist_data_with_ema = api._calculate_ema(hist_data.copy(), ema_period_val)
                                if not hist_data_with_ema.empty and len(hist_data_with_ema) >= ema_period_val:
                                    latest_ema = hist_data_with_ema.iloc[-1][f'EMA_{ema_period_val}']
                                    
                                    if ema_condition_val == "价格在EMA上方" and not (current_price > latest_ema):
                                        keep_stock = False
                                    elif ema_condition_val == "价格在EMA下方" and not (current_price < latest_ema):
                                        keep_stock = False
                                    elif ema_condition_val == "EMA向上":
                                        # Check if EMA is increasing over a short period (e.g., last 3 days)
                                        if len(hist_data_with_ema) < ema_period_val + 3: # Need enough data for EMA and trend
                                            keep_stock = False
                                        else:
                                            ema_series = hist_data_with_ema[f'EMA_{ema_period_val}'].dropna()
                                            if len(ema_series) < 3 or not (ema_series.iloc[-1] > ema_series.iloc[-2] > ema_series.iloc[-3]):
                                                keep_stock = False
                                    elif ema_condition_val == "EMA向下":
                                        # Check if EMA is decreasing over a short period (e.g., last 3 days)
                                        if len(hist_data_with_ema) < ema_period_val + 3: # Need enough data for EMA and trend
                                            keep_stock = False
                                        else:
                                            ema_series = hist_data_with_ema[f'EMA_{ema_period_val}'].dropna()
                                            if len(ema_series) < 3 or not (ema_series.iloc[-1] < ema_series.iloc[-2] < ema_series.iloc[-3]):
                                                keep_stock = False
                                else:
                                    keep_stock = False # Not enough data for EMA or calculation failed
                        else:
                            keep_stock = False # No historical data for this stock

                        if keep_stock:
                            stocks_to_keep.append(row)
                        
                        progress_bar.progress((i + 1) / total_stocks)
                    
                    filtered_data = pd.DataFrame(stocks_to_keep)
                    progress_bar.empty() # Clear the progress bar

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

with tab8:
    st.header("策略回测与模拟")
    st.markdown("根据技术指标设计策略，模拟交易并对比基准")

    # 时间周期选择器
    st.subheader("回测时间周期")
    col_start, col_end = st.columns(2)
    with col_start:
        strategy_start_date = st.date_input(
            "策略开始日期",
            value=datetime.now() - timedelta(days=365 * 5), # 默认5年前
            max_value=datetime.now(),
            key='strategy_start_date'
        )
    with col_end:
        strategy_end_date = st.date_input(
            "策略结束日期",
            value=datetime.now(),
            max_value=datetime.now(),
            key='strategy_end_date'
        )

    st.subheader("策略参数")
    strategy_symbol = st.text_input("回测股票代码 (美股)", value="AAPL", help="输入美股代码，如：AAPL, MSFT")
    initial_capital = st.number_input("期初资金 (USD)", min_value=100.0, value=10000.0, step=100.0)

    # 技术指标参数
    st.markdown("---")
    st.subheader("技术指标设置")

    # Bollinger Bands
    st.markdown("#### 布林带 (Bollinger Bands)")
    bb_period = st.slider("BB周期", min_value=5, max_value=50, value=20, step=1)
    bb_std_dev = st.slider("BB标准差", min_value=1.0, max_value=3.0, value=2.0, step=0.1)

    # MACD
    st.markdown("#### MACD (Moving Average Convergence Divergence)")
    macd_fast_period = st.slider("MACD快线周期", min_value=5, max_value=30, value=12, step=1)
    macd_slow_period = st.slider("MACD慢线周期", min_value=10, max_value=60, value=26, step=1)
    macd_signal_period = st.slider("MACD信号线周期", min_value=5, max_value=20, value=9, step=1)

    # RSI
    st.markdown("#### RSI (Relative Strength Index)")
    rsi_period = st.slider("RSI周期", min_value=5, max_value=30, value=14, step=1)
    rsi_oversold = st.slider("RSI超卖阈值", min_value=10, max_value=40, value=30, step=1)
    rsi_overbought = st.slider("RSI超买阈值", min_value=60, max_value=90, value=70, step=1)

    if st.button("运行策略回测", type="primary", key='run_strategy_backtest'):
        with st.spinner("正在获取数据并运行策略..."):
            # 1. 获取股票数据
            # 尝试从us2_stock_data_temp.csv加载数据，如果不存在则通过API获取
            # 注意：us2_stock_data_temp.csv是日级数据，如果需要日内数据，需要调用get_time_series_intraday
            # 1. 获取股票数据
            # 从us2_stock_data_temp.csv加载数据
            try:
                all_us_stock_data = pd.read_csv('us2_stock_data_temp.csv', encoding='utf-8-sig')
                all_us_stock_data['日期'] = pd.to_datetime(all_us_stock_data['日期'])

                # 筛选指定股票代码的数据
                stock_data = all_us_stock_data[all_us_stock_data['股票代码'] == strategy_symbol].copy()
                
                # 筛选日期范围
                stock_data = stock_data[
                    (stock_data['日期'] >= pd.to_datetime(strategy_start_date)) &
                    (stock_data['日期'] <= pd.to_datetime(strategy_end_date))
                ]
                
                if stock_data.empty:
                    st.error(f"在 'us2_stock_data_temp.csv' 中未能找到 {strategy_symbol} 在指定日期范围内的历史数据。")
                    # No return here, let the script continue to the end of the 'with st.spinner' block
            except FileNotFoundError:
                st.error("未找到 'us2_stock_data_temp.csv' 文件。请确保文件存在。")
                # No return here
            except Exception as e:
                st.error(f"加载或处理 'us2_stock_data_temp.csv' 文件时发生错误: {e}")
                # No return here

            # Only proceed if stock_data is valid after loading attempts
            if stock_data is not None and not stock_data.empty and 'close' in stock_data.columns:
                # 2. 计算技术指标
                df = stock_data.copy()
                df.set_index('日期', inplace=True)
                df.sort_index(inplace=True)

            # 计算布林带
            df = calculate_bollinger_bands(df, bb_period, bb_std_dev)
            # 计算中轨的5日均线，用于判断中轨趋势
            df[f'SMA_{bb_period}_Middle_Band_SMA_5'] = df['close'].rolling(window=5).mean()

            # 计算MACD
            # EMA for MACD
            df[f'EMA_Fast_{macd_fast_period}'] = df['close'].ewm(span=macd_fast_period, adjust=False).mean()
            df[f'EMA_Slow_{macd_slow_period}'] = df['close'].ewm(span=macd_slow_period, adjust=False).mean()
            df['MACD'] = df[f'EMA_Fast_{macd_fast_period}'] - df[f'EMA_Slow_{macd_slow_period}']
            df['Signal'] = df['MACD'].ewm(span=macd_signal_period, adjust=False).mean()
            df['Histogram'] = df['MACD'] - df['Signal']

            # 计算RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))

            # Debugging: Display indicators
            st.subheader("调试信息：技术指标")
            st.dataframe(df[['close', 'RSI', 'MACD', 'Signal', 'Histogram', f'UpperBB_{bb_period}_{bb_std_dev}', f'LowerBB_{bb_period}_{bb_std_dev}', f'SMA_{bb_period}', f'SMA_{bb_period}_Middle_Band_SMA_5']].tail())

            # 3. 策略模拟
            # 初始资金
            cash = initial_capital
            shares = 0
            portfolio_value = []
            buy_dates = []
            sell_dates = []

            # --- 初始买入逻辑 ---
            # 找到第一个非NaN的收盘价进行初始买入
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
                        # Removed debug message: st.success(f"初始买入！日期: {first_trade_date.strftime('%Y-%m-%d')}, 价格: {first_trade_price:.2f}, 数量: {initial_shares_to_buy}")
            # --- 初始买入逻辑结束 ---

            # 从第一个交易日开始模拟，或者从指标计算完成后的第一个有效日期开始
            start_loop_index = df.index.get_loc(first_tradable_index) if first_tradable_index is not None else 0
            # 确保从有足够历史数据计算指标的日期开始
            # 找到第一个RSI, MACD, Signal, BOLL不为NaN的索引
            first_valid_indicator_index = df[['RSI', 'MACD', 'Signal', f'UpperBB_{bb_period}_{bb_std_dev}', f'LowerBB_{bb_period}_{bb_std_dev}', f'SMA_{bb_period}', f'SMA_{bb_period}_Middle_Band_SMA_5']].dropna().index.min()
            if first_valid_indicator_index is not None:
                start_loop_index = max(start_loop_index, df.index.get_loc(first_valid_indicator_index))
            
            # 填充初始值，直到循环开始
            for i in range(start_loop_index):
                portfolio_value.append(cash + shares * df['close'].iloc[i])

            for i in range(start_loop_index, len(df)):
                current_date = df.index[i]
                prev_date = df.index[i-1]

                # 确保有足够的历史数据来计算指标
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


                # --- 买入条件 ---
                # BOLL 条件：价格从下轨下方回升至下轨与中轨之间，且中轨呈向上趋势
                boll_buy_condition = (prev_close < lower_bb and current_close >= lower_bb and current_close < middle_bb and
                                      middle_bb > prev_middle_bb_sma_5) # Simplified middle band trend check

                # MACD 条件：MACD 线在零轴下方或附近出现金叉，且柱状线由绿转红
                macd_buy_condition = (current_macd > current_signal and prev_macd <= prev_signal and # Golden cross
                                      current_histogram > 0 and prev_histogram <= 0) # Histogram turns from green to red (negative to positive)

                # RSI 条件：RSI 指标从 30 以下回升至 30-50 区间
                rsi_buy_condition = (prev_rsi < rsi_oversold and current_rsi >= rsi_oversold and current_rsi <= 50)

                # 最终买入条件
                if (boll_buy_condition and macd_buy_condition and rsi_buy_condition and cash > 0):
                    buy_price = current_close
                    shares_to_buy = cash // buy_price
                    if shares_to_buy > 0:
                        shares += shares_to_buy
                        cash -= shares_to_buy * buy_price
                        buy_dates.append(current_date)
                        # Removed debug message: st.success(f"买入！日期: {current_date.strftime('%Y-%m-%d')}, 价格: {buy_price:.2f}, 数量: {shares_to_buy}")

                # --- 卖出条件 ---
                # BOLL 条件：价格从上轨上方回落至上轨与中轨之间，且中轨呈向下趋势
                boll_sell_condition = (current_close > upper_bb) # Simplified middle band trend check

                # MACD 条件：MACD 线在零轴上方或附近出现死叉，且柱状线由红转绿
                macd_sell_condition = (current_macd < current_signal and prev_macd >= prev_signal and # Death cross
                                       current_histogram < 0 and prev_histogram >= 0) # Histogram turns from red to green (positive to negative)

                # RSI 条件：RSI 指标从 70 以上回落至 50-70 区间
                rsi_sell_condition = (current_rsi >= rsi_overbought)

                # 最终卖出条件
                if (boll_sell_condition and macd_sell_condition and rsi_sell_condition and shares > 0):
                    sell_price = current_close
                    cash += shares * sell_price
                    shares = 0 # 全部卖出
                    sell_dates.append(current_date)
                    # Removed debug message: st.warning(f"卖出！日期: {current_date.strftime('%Y-%m-%d')}, 价格: {sell_price:.2f}")
                
                portfolio_value.append(cash + shares * df['close'].iloc[i])
            
            strategy_df = pd.DataFrame({
                '日期': df.index, # Corrected to use start_loop_index
                '策略资金': portfolio_value
            })
            strategy_df.set_index('日期', inplace=True)
            # strategy_df['策略_归一化'] = strategy_df['策略资金'] / initial_capital * 100.0 # Remove normalization

            # 4. 获取基准数据 (SPY, QQQ)
            benchmarks = ['SPY', 'QQQ']
            benchmark_dfs = {}
            for bench_symbol in benchmarks:
                bench_data = get_cached_stock_data( # Using the cached function
                    symbol=bench_symbol,
                    market='us2',
                    start_date=strategy_start_date.strftime('%Y-%m-%d'),
                    end_date=strategy_end_date.strftime('%Y-%m-%d'),
                    period='daily',
                    adjust='qfq'
                )
                if bench_data is not None and not bench_data.empty and 'close' in bench_data.columns:
                    bench_data.set_index('日期', inplace=True)
                    bench_data.sort_index(inplace=True)
                    # 对齐日期到策略数据
                    aligned_bench_data = pd.merge(strategy_df.index.to_frame(), bench_data[['close']], left_index=True, right_index=True, how='inner')
                    if not aligned_bench_data.empty:
                        # Calculate absolute value for benchmark, starting with initial_capital
                        initial_bench_price = aligned_bench_data['close'].iloc[0]
                        aligned_bench_data['绝对资金'] = (aligned_bench_data['close'] / initial_bench_price) * initial_capital
                        benchmark_dfs[bench_symbol] = aligned_bench_data['绝对资金']
                else:
                    st.warning(f"未能获取基准 {bench_symbol} 的数据。")

            # 5. 绘制资金成长曲线
            fig_strategy = go.Figure()
            fig_strategy.add_trace(go.Scatter(x=strategy_df.index, y=strategy_df['策略资金'], mode='lines', name=f'{strategy_symbol} 策略 ({initial_capital:.0f} USD)'))

            for bench_symbol, bench_series in benchmark_dfs.items():
                fig_strategy.add_trace(go.Scatter(x=bench_series.index, y=bench_series, mode='lines', name=f'基准 {bench_symbol}'))

            fig_strategy.update_layout(
                title=f"{strategy_symbol} 策略回测 vs 基准 ({strategy_start_date.strftime('%Y-%m-%d')} - {strategy_end_date.strftime('%Y-%m-%d')})",
                xaxis_title="日期",
                yaxis_title="绝对资金 (USD)", # Changed Y-axis title
                hovermode="x unified",
                height=600
            )
            st.plotly_chart(fig_strategy, use_container_width=True)

            st.subheader("策略交易详情")
            st.dataframe(df.head()) # Display first 5 rows of data with indicators

            st.subheader("交易记录")
            if buy_dates:
                st.write(f"买入日期: {buy_dates}")
            else:
                st.write("无买入记录。")
            if sell_dates:
                st.write(f"卖出日期: {sell_dates}")
            else:
                st.write("无卖出记录。")
            
            st.write(f"期末现金: {cash:.2f} USD")
            st.write(f"期末持股: {shares} 股")
            if not df.empty:
                st.write(f"期末股票价值: {shares * df['close'].iloc[-1]:.2f} USD")
                st.write(f"期末总资产: {cash + shares * df['close'].iloc[-1]:.2f} USD")
            
            st.subheader("数据尾部 (包含指标)")
            st.dataframe(df.tail())

#---
