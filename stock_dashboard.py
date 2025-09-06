import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import yfinance as yf
from api import get_stock_finance_data
import plotly.express as px
import plotly.graph_objects as go

# 页面配置
st.set_page_config(
    page_title="男大自用金融看板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 侧边栏导航
st.sidebar.title("📊 股票分析看板")
st.sidebar.markdown("---")

# 模块选择
module = st.sidebar.selectbox(
    "选择功能模块",
    ["股票查询", "我的自选", "股票分析","策略模拟"],
    index=0
)

# 股票查询模块
if module == "股票查询":
    st.title("🔍 股票查询")
    st.markdown("---")
    
    # 查询输入
    col1, col2 = st.columns([2, 1])
    
    with col1:
        stock_code = st.text_input(
            "请输入股票代码",
            placeholder="例如：000001.SZ, 600000.SS, AAPL",
            help="支持A股（如000001.SZ）和美股（如AAPL）"
        )
    
    with col2:
        query_btn = st.button("查询", type="primary", use_container_width=True)
    
    if query_btn and stock_code:
        try:
            # 使用yfinance获取股票数据
            with st.spinner("正在获取股票数据..."):
                ticker = yf.Ticker(stock_code)
                
                # 获取基本信息
                info = ticker.info
                
                # 获取历史数据（最近30天）
                hist = ticker.history(period="1mo")
                
                if not hist.empty:
                    # 显示基本信息
                    st.success(f"成功获取 {stock_code} 的数据")
                    
                    # 创建两列布局
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.subheader("📊 基本信息")
                        basic_info = {
                            "股票名称": info.get('longName', 'N/A'),
                            "当前价格": f"${info.get('currentPrice', 'N/A')}",
                            "涨跌幅": f"{info.get('regularMarketChangePercent', 'N/A')}%",
                            "市值": f"${info.get('marketCap', 'N/A'):,}" if info.get('marketCap') else 'N/A',
                            "市盈率": info.get('trailingPE', 'N/A'),
                            "52周最高": f"${info.get('fiftyTwoWeekHigh', 'N/A')}",
                            "52周最低": f"${info.get('fiftyTwoWeekLow', 'N/A')}"
                        }
                        
                        for key, value in basic_info.items():
                            st.metric(key, value)
                    
                    with col2:
                        st.subheader("📈 价格走势")
                        # 绘制价格走势图
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=hist.index,
                            y=hist['Close'],
                            mode='lines',
                            name='收盘价',
                            line=dict(color='blue', width=2)
                        ))
                        fig.update_layout(
                            title=f"{stock_code} 近30天价格走势",
                            xaxis_title="日期",
                            yaxis_title="价格 ($)",
                            height=400
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # 显示最近5天数据
                    st.subheader("📋 最近5天数据")
                    recent_data = hist.tail(5)[['Open', 'High', 'Low', 'Close', 'Volume']]
                    recent_data.columns = ['开盘价', '最高价', '最低价', '收盘价', '成交量']
                    st.dataframe(recent_data, use_container_width=True)
                    
                else:
                    st.error("未找到该股票的数据，请检查股票代码是否正确")
                    
        except Exception as e:
            st.error(f"查询失败：{str(e)}")
            st.info("请确保股票代码格式正确，A股格式：000001.SZ，美股格式：AAPL")

# 我的自选模块
elif module == "我的自选":
    st.title("⭐ 我的自选")
    st.markdown("---")
    
    # 自选股列表（可以后续扩展为可编辑）
    watchlist = [
        {"code": "000001.SZ", "name": "平安银行", "sector": "银行"},
        {"code": "000002.SZ", "name": "万科A", "sector": "房地产"},
        {"code": "600000.SS", "name": "浦发银行", "sector": "银行"},
        {"code": "600036.SS", "name": "招商银行", "sector": "银行"},
        {"code": "000858.SZ", "name": "五粮液", "sector": "白酒"},
        {"code": "AAPL", "name": "苹果", "sector": "科技"},
        {"code": "TSLA", "name": "特斯拉", "sector": "汽车"},
        {"code": "MSFT", "name": "微软", "sector": "科技"}
    ]
    
    # 添加/删除自选股功能
    with st.expander("管理自选股", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            new_code = st.text_input("添加股票代码", placeholder="例如：000001.SZ")
        with col2:
            if st.button("添加"):
                if new_code:
                    try:
                        ticker = yf.Ticker(new_code)
                        info = ticker.info
                        name = info.get('longName', 'Unknown')
                        watchlist.append({"code": new_code, "name": name, "sector": "Unknown"})
                        st.success(f"已添加 {new_code}")
                        st.rerun()
                    except:
                        st.error("添加失败，请检查股票代码")
    
    # 获取自选股数据
    if st.button("刷新数据", type="primary"):
        with st.spinner("正在获取自选股数据..."):
            watchlist_data = []
            
            for stock in watchlist:
                try:
                    ticker = yf.Ticker(stock["code"])
                    hist = ticker.history(period="2d")  # 获取最近2天数据
                    
                    if not hist.empty:
                        latest = hist.iloc[-1]
                        prev = hist.iloc[-2] if len(hist) > 1 else latest
                        
                        # 计算振幅
                        amplitude = ((latest['High'] - latest['Low']) / prev['Close'] * 100) if prev['Close'] > 0 else 0
                        
                        watchlist_data.append({
                            "股票代码": stock["code"],
                            "股票名称": stock["name"],
                            "行业": stock["sector"],
                            "开盘价": f"${latest['Open']:.2f}",
                            "收盘价": f"${latest['Close']:.2f}",
                            "最高价": f"${latest['High']:.2f}",
                            "最低价": f"${latest['Low']:.2f}",
                            "振幅": f"{amplitude:.2f}%",
                            "成交量": f"{latest['Volume']:,}",
                            "涨跌幅": f"{((latest['Close'] - prev['Close']) / prev['Close'] * 100):.2f}%" if prev['Close'] > 0 else "0.00%"
                        })
                except Exception as e:
                    st.warning(f"获取 {stock['code']} 数据失败: {str(e)}")
            
            if watchlist_data:
                df_watchlist = pd.DataFrame(watchlist_data)
                st.subheader("📊 自选股数据")
                st.dataframe(df_watchlist, use_container_width=True)
                
                # 保存到session state
                st.session_state['watchlist_data'] = df_watchlist
            else:
                st.error("未能获取任何自选股数据")
    
    # 显示已保存的数据
    if 'watchlist_data' in st.session_state:
        st.subheader("📊 自选股数据")
        st.dataframe(st.session_state['watchlist_data'], use_container_width=True)
        
        # 简单的统计图表
        col1, col2 = st.columns(2)
        
        with col1:
            # 涨跌幅分布
            if '涨跌幅' in st.session_state['watchlist_data'].columns:
                df = st.session_state['watchlist_data'].copy()
                df['涨跌幅数值'] = df['涨跌幅'].str.replace('%', '').astype(float)
                
                fig = px.bar(
                    df, 
                    x='股票名称', 
                    y='涨跌幅数值',
                    title='自选股涨跌幅分布',
                    color='涨跌幅数值',
                    color_continuous_scale=['red', 'white', 'green']
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # 成交量对比
            if '成交量' in st.session_state['watchlist_data'].columns:
                df = st.session_state['watchlist_data'].copy()
                df['成交量数值'] = df['成交量'].str.replace(',', '').astype(float)
                
                fig = px.pie(
                    df, 
                    values='成交量数值', 
                    names='股票名称',
                    title='自选股成交量分布'
                )
                st.plotly_chart(fig, use_container_width=True)

# 数据分析模块
elif module == "数据分析":
    st.title("📊 数据分析")
    st.markdown("---")
    
    st.info("数据分析模块正在开发中，敬请期待...")
    
    # 占位内容
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("总自选股", "8", "0")
    
    with col2:
        st.metric("今日上涨", "5", "2")
    
    with col3:
        st.metric("今日下跌", "3", "-1")
    
    # 示例图表
    st.subheader("示例分析图表")
    
    # 创建示例数据
    sample_data = pd.DataFrame({
        '日期': pd.date_range('2024-01-01', periods=30),
        '价格': [100 + i + (i % 3) * 2 for i in range(30)],
        '成交量': [1000 + i * 50 for i in range(30)]
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig1 = px.line(sample_data, x='日期', y='价格', title='示例价格走势')
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = px.bar(sample_data, x='日期', y='成交量', title='示例成交量')
        st.plotly_chart(fig2, use_container_width=True)

# 页脚
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>📈 股票分析看板 | 数据来源：Yahoo Finance | 仅供参考，投资有风险</p>
    </div>
    """,
    unsafe_allow_html=True
)
