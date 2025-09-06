import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from api import StockDataAPI, get_stock_data, get_market_list


"""主函数"""
st.set_page_config(
page_title="股票数据获取Dashboard",
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
tab1, tab2, tab3, tab4 = st.tabs(["📊 股票数据", "📋 市场列表", "📈 图表分析", "ℹ️ 使用说明"])

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
    st.header("使用说明")

    st.markdown("""
    ### 📖 功能说明

    **1. 股票数据获取**
    - 支持上证、深证、创业板、美股数据获取
    - 可选择不同的时间周期（日线、周线、月线）
    - 支持前复权、后复权、不复权数据

    **2. 市场列表**
    - 查看各市场的股票列表
    - 支持按代码或名称搜索股票

    **3. 图表分析**
    - K线图显示价格走势
    - 成交量分析
    - 涨跌幅分布统计

    ### 🔧 参数说明

    **市场类型：**
    - `sh`: 上证（上海证券交易所）
    - `sz`: 深证（深圳证券交易所）
    - `cyb`: 创业板
    - `us`: 美股（美国股市）

    **股票代码格式：**
    - A股：直接输入代码，如 `000001`, `600000`
    - 美股：输入英文代码，如 `AAPL`, `MSFT`

    **数据周期：**
    - `daily`: 日线数据
    - `weekly`: 周线数据
    - `monthly`: 月线数据

    **复权类型：**
    - `qfq`: 前复权（推荐）
    - `hfq`: 后复权
    - ``: 不复权

    ### ⚠️ 注意事项

    1. 数据获取可能需要一些时间，请耐心等待
    2. 部分股票可能因停牌等原因无法获取数据
    3. 美股数据可能因时差问题有延迟
    4. 建议使用较短的日期范围以提高获取速度
    """)


#------------------

"""

## 📁 文件说明

1. **`stock_data_api.py`** - 核心API类
   - `StockDataAPI` 类：支持上证、深证、创业板、美股数据获取
   - 便捷函数：`get_stock_data()`, `get_market_list()`, `get_realtime_data()`
   - 支持时间范围、symbol、周期、复权等参数

2. **`stock_data_example.py`** - 使用示例
   - 演示各种数据获取功能
   - 测试不同参数组合
   - 批量获取多只股票数据

3. **`stock_data_dashboard.py`** - Streamlit Dashboard
   - 可视化界面展示数据获取功能
   - 支持图表分析和数据展示
   - 交互式参数设置

4. **`requirements.txt`** - 更新了依赖
   - 添加了 `akshare>=1.12.0` 依赖

## 🚀 主要功能

### 1. 数据获取功能
- **上证数据**: `get_stock_data('000001', 'sh')`
- **深证数据**: `get_stock_data('399001', 'sz')`  
- **创业板数据**: `get_stock_data('399006', 'cyb')`
- **美股数据**: `get_stock_data('AAPL', 'us')`

### 2. 参数支持
- **时间范围**: `start_date`, `end_date` (格式: 'YYYY-MM-DD')
- **股票代码**: `symbol` (自动处理市场后缀)
- **数据周期**: `period` ('daily', 'weekly', 'monthly')
- **复权类型**: `adjust` ('qfq', 'hfq', '')

### 3. 其他功能
- 市场股票列表获取
- 实时数据获取
- 数据格式化和清洗
- 错误处理和异常捕获

## 📖 使用方法

```python
from stock_data_api import get_stock_data

# 获取上证指数数据
data = get_stock_data('000001', 'sh', '2024-01-01', '2024-12-31')

# 获取美股苹果公司数据
data = get_stock_data('AAPL', 'us', '2024-01-01', '2024-12-31')

# 获取周线数据
data = get_stock_data('000001', 'sh', period='weekly')
```

运行Streamlit Dashboard：
```bash
<code_block_to_apply_changes_from>
```

这个接口设计考虑了时间、symbol作为核心参数，支持多个市场，并提供了完整的错误处理和数据处理功能。
"""