import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Union
import warnings
#from tqdm import tqdm
import requests # Added for Alpha Vantage API calls
import json # Added for Alpha Vantage API calls

warnings.filterwarnings('ignore')
#tqdm.disable = True

class StockDataAPI:
    """股票数据获取API类，支持上证、深证、创业板、美股数据获取"""
    
    def __init__(self):
        self.market_mapping = {
            'sh': '上证',  # 上海证券交易所
            'sz': '深证',  # 深圳证券交易所  
            'cyb': '创业板',  # 创业板
            'us': '美股'   # 美国股市
        }
    
    def get_stock_data(self, 
                      symbol: str, 
                      market: str = 'sh',
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      period: str = 'daily',
                      adjust: str = 'qfq') -> Optional[pd.DataFrame]:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            market: 市场类型 ('sh', 'sz', 'cyb', 'us')
            start_date: 开始日期，格式：'YYYY-MM-DD'
            end_date: 结束日期，格式：'YYYY-MM-DD'
            period: 数据周期 ('daily', 'weekly', 'monthly')
            adjust: 复权类型 ('qfq': 前复权, 'hfq': 后复权, '': 不复权)
        
        Returns:
            DataFrame: 包含股票数据的DataFrame
        """
        try:
            # 设置默认日期范围（最近一年）
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            else:
                start_date = start_date.replace('-', '')
            
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            else:
                end_date = end_date.replace('-', '')
            
            # 根据市场类型获取数据
            if market == 'sh':
                return self._get_shanghai_data(symbol, start_date, end_date, period, adjust)
            elif market == 'sz':
                return self._get_shenzhen_data(symbol, start_date, end_date, period, adjust)
            elif market == 'cyb':
                return self._get_chinext_data(symbol, start_date, end_date, period, adjust)
            elif market == 'us':
                return self._get_us_data(symbol, start_date, end_date, period, adjust)
            elif market == 'us2':
                return self._get_us_data_sn(symbol, adjust)
            else:
                raise ValueError(f"不支持的市场类型: {market}")
                
        except Exception as e:
            print(f"获取股票数据失败: {str(e)}")
            return None
    
    def _get_shanghai_data(self, symbol: str, start_date: str, end_date: str, 
                          period: str, adjust: str) -> pd.DataFrame:
        """获取上海证券交易所数据"""
        # 确保股票代码格式正确
        # if not symbol.endswith('.SH'):
        #     symbol = f"{symbol}.SH"
        
        # 获取股票历史数据
        df = ak.stock_zh_a_hist(symbol=symbol, period=period, 
                               start_date=start_date, end_date=end_date, adjust=adjust)
        
        # 数据清洗和格式化
        df = self._format_dataframe(df, '上证')
        return df
    
    def _get_shenzhen_data(self, symbol: str, start_date: str, end_date: str,
                          period: str, adjust: str) -> pd.DataFrame:
        """获取深圳证券交易所数据"""
        # 确保股票代码格式正确
        # if not symbol.endswith('.SZ'):
        #     symbol = f"{symbol}.SZ"
        
        # 获取股票历史数据
        df = ak.stock_zh_a_hist(symbol=symbol, period=period,
                               start_date=start_date, end_date=end_date, adjust=adjust)
        
        # 数据清洗和格式化
        df = self._format_dataframe(df, '深证')
        return df
    
    def _get_chinext_data(self, symbol: str, start_date: str, end_date: str,
                         period: str, adjust: str) -> pd.DataFrame:
        """获取创业板数据"""
        # 确保股票代码格式正确
        # if not symbol.endswith('.SZ'):
        #     symbol = f"{symbol}.SZ"
        
        # 获取股票历史数据
        df = ak.stock_zh_a_hist(symbol=symbol, period=period,
                               start_date=start_date, end_date=end_date, adjust=adjust)
        
        # 数据清洗和格式化
        df = self._format_dataframe(df, '创业板')
        return df
    
    def _get_us_data(self, symbol: str, start_date: str, end_date: str,
                    period: str, adjust: str) -> pd.DataFrame:
        """获取美股数据"""
        # 转换日期格式
        start_date_us = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
        end_date_us = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"

        # 仅支持三种前缀：105. / 106. / 107.
        user_raw = (symbol or "").strip().upper()
        base = user_raw.split('.')[-1] if '.' in user_raw else user_raw
        # 允许点/横杠两种写法
        forms = {base, base.replace('.', '-'), base.replace('-', '.')}
        cand_hist = []
        for form in forms:
            for px in ["105", "106", "107"]:
                cand_hist.append(f"{px}.{form}")
        # 去重并尝试
        tried = set()
        for cand in cand_hist:
            sc = cand.strip()
            if not sc or sc in tried:
                continue
            tried.add(sc)
            try:
                df = ak.stock_us_hist(symbol=sc, period=period,
                                      start_date=start_date_us, end_date=end_date_us, adjust=adjust)
                #df = ak.stock_us_daily(symbol=sc)
                if df is not None and not df.empty:
                    return self._format_dataframe(df, '美股')
            except Exception:
                continue

        # 未获取到
        return pd.DataFrame()
    
    def _get_us_data_sn(self, symbol: str, adjust: str):
        try:
            df = ak.stock_us_daily(symbol=symbol, adjust=adjust)
            if df is not None and not df.empty:
                return self._format_dataframe(df, '美股')
        except Exception as e:
            print(e)

    def _format_dataframe(self, df: pd.DataFrame, market: str) -> pd.DataFrame:
        """格式化DataFrame"""
        if df is None or df.empty:
            return df
        
        print(f"原始数据列名: {df.columns.tolist()}")
        
        # 处理日期列 - 检查多种可能的列名
        date_columns = ['日期', 'date', 'Date', 'datetime', '时间']
        date_col = None
        
        for col in date_columns:
            if col in df.columns:
                date_col = col
                break
        
        if date_col:
            # 重命名为统一的'日期'列
            if date_col != '日期':
                df.rename(columns={date_col: '日期'}, inplace=True)
            df['日期'] = pd.to_datetime(df['日期'])
        else:
            print(f"警告: 未找到日期列，可用列名: {df.columns.tolist()}")
            # 如果没有找到日期列，尝试使用第一列作为日期
            if len(df.columns) > 0:
                first_col = df.columns[0]
                df.rename(columns={first_col: '日期'}, inplace=True)
                try:
                    df['日期'] = pd.to_datetime(df['日期'])
                except:
                    print(f"无法将第一列 {first_col} 转换为日期")
        
        # 添加市场信息
        df['市场'] = market
        
        # 确保数值列为float类型
        numeric_columns = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '振幅', '涨跌幅', '涨跌额', '换手率',
                          'open', 'close', 'high', 'low', 'volume', 'amount', 'pct_chg', 'change']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 按日期排序（如果存在日期列）
        if '日期' in df.columns:
            df = df.sort_values('日期').reset_index(drop=True)
        
        print(f"格式化后数据列名: {df.columns.tolist()}")
        return df
    
    def get_market_list(self, market: str = 'sh') -> Optional[pd.DataFrame]:
        """
        获取市场股票列表
        
        Args:
            market: 市场类型 ('sh', 'sz', 'cyb', 'us')
        
        Returns:
            DataFrame: 包含股票列表的DataFrame
        """
        try:
            if market == 'sh':
                # 获取上证A股列表
                df = ak.stock_sh_a_spot_em()
            elif market == 'sz':
                # 获取深证A股列表
                df = ak.stock_sz_a_spot_em()
            elif market == 'cyb':
                # 获取创业板股票列表
                df = ak.stock_cy_a_spot_em()
            elif market == 'us':
                # 获取美股列表
                df = ak.stock_us_spot_em()
            else:
                raise ValueError(f"不支持的市场类型: {market}")
            
            return df
            
        except Exception as e:
            print(f"获取市场列表失败: {str(e)}")
            return None
    
    def get_realtime_data(self, symbol: str, market: str = 'sh') -> Optional[pd.DataFrame]:
        """
        获取实时股票数据
        
        Args:
            symbol: 股票代码
            market: 市场类型 ('sh', 'sz', 'cyb', 'us')
        
        Returns:
            DataFrame: 包含实时数据的DataFrame
        """
        try:
            if market in ['sh', 'sz', 'cyb']:
                # A股实时数据
                if market == 'sh' and not symbol.endswith('.SH'):
                    symbol = f"{symbol}.SH"
                elif market in ['sz', 'cyb'] and not symbol.endswith('.SZ'):
                    symbol = f"{symbol}.SZ"
                
                df = ak.stock_zh_a_spot_em()
                df = df[df['代码'] == symbol.split('.')[0]]
                
            elif market == 'us':
                # 美股实时数据
                df = ak.stock_us_spot_em()
                df = df[df['代码'] == symbol]
            
            return df
            
        except Exception as e:
            print(f"获取实时数据失败: {str(e)}")
            return None

    def get_screener_data(self, market: str = 'sh') -> Optional[pd.DataFrame]:
        """
        获取用于股票筛选器的实时数据，包含当前价格、涨跌幅、总市值、市盈率等
        
        Args:
            market: 市场类型 ('sh', 'sz', 'cyb', 'us')
        
        Returns:
            DataFrame: 包含筛选所需数据的DataFrame
        """
        try:
            df = None
            if market == 'sh':
                df = ak.stock_sh_a_spot_em()
            elif market == 'sz':
                df = ak.stock_sz_a_spot_em()
            elif market == 'cyb':
                df = ak.stock_cy_a_spot_em()
            elif market == 'us':
                df = ak.stock_us_spot_em()
            else:
                raise ValueError(f"不支持的市场类型: {market}")
            
            if df is not None and not df.empty:
                # 统一列名以便筛选
                column_mapping = {
                    '最新价': '当前价格',
                    '涨跌幅': '涨跌幅',
                    '总市值': '当前市值',
                    '成交量': '交易量',
                    '市盈率-动态': '当前P/E',
                    '代码': '股票代码',
                    '名称': '股票名称'
                }
                df.rename(columns=column_mapping, inplace=True)
                
                # 确保数值列为float类型
                numeric_cols = ['当前价格', '涨跌幅', '当前市值', '交易量', '当前P/E']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df[['股票代码', '股票名称', '当前价格', '涨跌幅', '当前市值', '交易量', '当前P/E']]
            return None
            
        except Exception as e:
            print(f"获取筛选数据失败: {str(e)}")
            return None

    def _calculate_ema(self, df: pd.DataFrame, period: int = 10) -> pd.DataFrame:
        """
        计算指数移动平均线 (Exponential Moving Average, EMA)
        要求DataFrame包含 '收盘' 列
        """
        if df is None or df.empty or '收盘' not in df.columns:
            return df
        
        df[f'EMA_{period}'] = df['收盘'].ewm(span=period, adjust=False).mean()
        
        return df

    def _get_time_series_intraday(self,
                                 symbol: str,
                                 interval: str = '15min',
                                 outputsize: str = 'compact') -> Optional[pd.DataFrame]:
        """
        获取股票的日内交易数据 (Alpha Vantage: TIME_SERIES_INTRADAY)

        Args:
            symbol: 股票代码 (e.g., 'IBM')
            interval: 时间间隔 ('1min', '5min', '15min', '30min', '60min')
            outputsize: 数据量 ('compact' for last 100 data points, 'full' for full-length)
            api_key: Alpha Vantage API 密钥

        Returns:
            DataFrame: 包含日内交易数据的DataFrame
        """
        global alpha_api
        if not alpha_api or alpha_api == 'YOUR_ALPHA_VANTAGE_API_KEY':
            print("错误: Alpha Vantage API 密钥未提供或为默认值。请设置您的API密钥。")
            return None

        base_url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": alpha_api,
            "datatype": "json"
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status() # 检查HTTP错误
            data = response.json()

            if "Time Series (Intraday)" not in data:
                print(f"获取 {symbol} 的日内数据失败: {data.get('Note', '未知错误')}")
                return None

            time_series = data["Time Series (Intraday)"]
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df = df.astype(float) # 将所有数据转换为浮点数

            # 格式化列名
            df.columns = ['开盘', '最高', '最低', '收盘', '成交量']
            df.index.name = '日期时间'
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            return df

        except requests.exceptions.RequestException as e:
            print(f"请求 Alpha Vantage API 失败: {e}")
            return None
        except json.JSONDecodeError:
            print("解析 Alpha Vantage API 响应失败。")
            return None
        except Exception as e:
            print(f"获取日内数据时发生未知错误: {e}")
            return None

# ===== 基金相关 =====
    def get_fund_nav(self,
                     fund_code: str,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     indicator: str = "单位净值走势") -> Optional[pd.DataFrame]:
        """
        获取开放式基金净值时间序列
        fund_code: 基金代码，如 110022
        indicator: "单位净值走势" 或 "累计净值走势"
        返回列通常包含：['日期', '单位净值', '累计净值', '涨跌幅']（视 indicator 而定）
        """
        try:
            df = ak.fund_open_fund_info_em(symbol=fund_code, indicator=indicator)
            if df is None or df.empty:
                return df
            # 统一日期列名
            if '日期' not in df.columns:
                for cand in ['净值日期', 'date', 'Date', '净值时间']:
                    if cand in df.columns:
                        df.rename(columns={cand: '日期'}, inplace=True)
                        break
            # 统一净值列名（尽可能保留原列，同时提供标准化列便于后续处理）
            if '单位净值' not in df.columns and 'nav' in df.columns:
                df.rename(columns={'nav': '单位净值'}, inplace=True)
            if '累计净值' not in df.columns and 'acc_nav' in df.columns:
                df.rename(columns={'acc_nav': '累计净值'}, inplace=True)
            # 类型转换与时间筛选
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'], errors='coerce')
            for col in ['单位净值', '累计净值']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            if start_date and '日期' in df.columns:
                df = df[df['日期'] >= pd.to_datetime(start_date)]
            if end_date and '日期' in df.columns:
                df = df[df['日期'] <= pd.to_datetime(end_date)]
            if '日期' in df.columns:
                df = df.sort_values('日期').reset_index(drop=True)
            return df
        except Exception as e:
            print(f"获取基金净值失败: {str(e)}")
            return None

    def get_open_fund_daily_list(self) -> Optional[pd.DataFrame]:
        """
        获取开放式基金日行情列表（快照）
        """
        try:
            df = ak.fund_open_fund_daily_em()
            return df
        except Exception as e:
            print(f"获取基金列表失败: {str(e)}")
            return None

    def get_index_history(self,
                          symbol: str,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None,
                          period: str = 'daily') -> Optional[pd.DataFrame]:
        """
        获取常用A股指数历史行情（用于基金基准）
        symbol 需为 eastmoney 样式：如 'sh000300', 'sh000016', 'sh000905', 'sh000852', 'sz399006'
        返回包含统一的 '日期'、'收盘' 列
        """
        try:
            df = ak.stock_zh_index_daily(symbol=symbol)
            if df is None or df.empty:
                return df
            # 统一列
            if 'date' in df.columns:
                df.rename(columns={'date': '日期'}, inplace=True)
                df['日期'] = pd.to_datetime(df['日期'])
            if 'close' in df.columns:
                df.rename(columns={'close': '收盘'}, inplace=True)
                df['收盘'] = pd.to_numeric(df['收盘'], errors='coerce')
            # 时间筛选
            if start_date:
                df = df[df['日期'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['日期'] <= pd.to_datetime(end_date)]
            # 排序
            df = df.sort_values('日期').reset_index(drop=True)
            return df[['日期', '收盘']]
        except Exception as e:
            print(f"获取指数行情失败: {str(e)}")
            return None

    def get_index_history_by_name(self,
                                  name: str,
                                  start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        按常见名称获取指数：上证50、沪深300、中证500、中证1000、创业板指
        """
        name_to_symbol = {
            '上证50': 'sh000016',
            '沪深300': 'sh000300',
            '中证500': 'sh000905',
            '中证1000': 'sh000852',
            '创业板指': 'sz399006',
        }
        symbol = name_to_symbol.get(name)
        if symbol is None:
            print(f"不支持的指数名称: {name}")
            return None
        return self.get_index_history(symbol=symbol, start_date=start_date, end_date=end_date)

# 便捷函数
def get_stock_data(symbol: str, 
                  market: str = 'sh',
                  start_date: Optional[str] = None,
                  end_date: Optional[str] = None,
                  period: str = 'daily',
                  adjust: str = 'qfq') -> Optional[pd.DataFrame]:
    """
    便捷函数：获取股票数据
    
    Args:
        symbol: 股票代码
        market: 市场类型 ('sh', 'sz', 'cyb', 'us')
        start_date: 开始日期，格式：'YYYY-MM-DD'
        end_date: 结束日期，格式：'YYYY-MM-DD'
        period: 数据周期 ('daily', 'weekly', 'monthly')
        adjust: 复权类型 ('qfq': 前复权, 'hfq': 后复权, '': 不复权)
    
    Returns:
        DataFrame: 包含股票数据的DataFrame
    """
    api = StockDataAPI()
    return api.get_stock_data(symbol, market, start_date, end_date, period, adjust)


def get_market_list(market: str = 'sh') -> Optional[pd.DataFrame]:
    """
    便捷函数：获取市场股票列表
    
    Args:
        market: 市场类型 ('sh', 'sz', 'cyb', 'us')
    
    Returns:
        DataFrame: 包含股票列表的DataFrame
    """
    api = StockDataAPI()
    return api.get_market_list(market)


def get_realtime_data(symbol: str, market: str = 'sh') -> Optional[pd.DataFrame]:
    """
    便捷函数：获取实时股票数据
    
    Args:
        symbol: 股票代码
        market: 市场类型 ('sh', 'sz', 'cyb', 'us')
    
    Returns:
        DataFrame: 包含实时数据的DataFrame
    """
    api = StockDataAPI()
    return api.get_realtime_data(symbol, market)

def get_screener_data(market: str = 'sh') -> Optional[pd.DataFrame]:
    """
    便捷函数：获取用于股票筛选器的实时数据
    """
    api = StockDataAPI()
    return api.get_screener_data(market)


def get_time_series_intraday(symbol: str,
                             interval: str = '15min',
                             outputsize: str = 'compact') -> Optional[pd.DataFrame]:
    """
    便捷函数：获取股票的日内交易数据 (Alpha Vantage: TIME_SERIES_INTRADAY)
    """
    api = StockDataAPI()
    return api._get_time_series_intraday(symbol, interval, outputsize)


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """
    计算布林带 (Bollinger Bands)
    要求DataFrame包含 '收盘' 列
    """
    if df is None or df.empty or 'close' not in df.columns:
        return df

    # 计算SMA (Middle Band)
    df[f'SMA_{period}'] = df['close'].rolling(window=period).mean()
    # 计算标准差
    df[f'STD_{period}'] = df['close'].rolling(window=period).std()
    # 计算上轨和下轨
    df[f'UpperBB_{period}_{std_dev}'] = df[f'SMA_{period}'] + (df[f'STD_{period}'] * std_dev)
    df[f'LowerBB_{period}_{std_dev}'] = df[f'SMA_{period}'] - (df[f'STD_{period}'] * std_dev)
    
    #print("函数内新增的列：", [col for col in df.columns if col in [f'SMA_{period}', f'STD_{period}', f'UpperBB_{period}_{std_dev}', f'LowerBB_{period}_{std_dev}']])
    return df

                            

# 使用示例
# if __name__ == "__main__":
#     # 创建API实例
#     api = StockDataAPI()
    
#     # 示例1：获取上证指数数据
#     print("=== 获取上证指数数据 ===")
#     sh_data = api.get_stock_data('000001', 'sh', '2024-01-01', '2024-12-31')
#     if sh_data is not None:
#         print(f"上证指数数据形状: {sh_data.shape}")
#         print(sh_data.head())
    
#     # 示例2：获取深证成指数据
#     print("\n=== 获取深证成指数据 ===")
#     sz_data = api.get_stock_data('399001', 'sz', '2024-01-01', '2024-12-31')
#     if sz_data is not None:
#         print(f"深证成指数据形状: {sz_data.shape}")
#         print(sz_data.head())
    
#     # 示例3：获取创业板指数据
#     print("\n=== 获取创业板指数据 ===")
#     cyb_data = api.get_stock_data('399006', 'cyb', '2024-01-01', '2024-12-31')
#     if cyb_data is not None:
#         print(f"创业板指数据形状: {cyb_data.shape}")
#         print(cyb_data.head())
    
#     # 示例4：获取美股数据（苹果公司）
#     print("\n=== 获取美股数据（苹果公司）===")
#     us_data = api.get_stock_data('AAPL', 'us', '2024-01-01', '2024-12-31')
#     if us_data is not None:
#         print(f"苹果公司数据形状: {us_data.shape}")
#         print(us_data.head())
    
#     # 示例5：获取市场股票列表
#     print("\n=== 获取上证A股列表 ===")
#     sh_list = api.get_market_list('sh')
#     if sh_list is not None:
#         print(f"上证A股数量: {len(sh_list)}")
#         print(sh_list.head())

#     # 示例6：获取日内交易数据 (Alpha Vantage)
#     print("\n=== 获取日内交易数据 (IBM, 5min) ===")
#     intraday_data = get_time_series_intraday(symbol='IBM', interval='5min', outputsize='compact')
#     if intraday_data is not None:
#         print(f"IBM 日内数据形状: {intraday_data.shape}")
#         print(intraday_data.head())
#     else:
#         print("未能获取 IBM 的日内交易数据。请检查API密钥和请求参数。")
