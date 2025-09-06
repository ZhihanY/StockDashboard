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
