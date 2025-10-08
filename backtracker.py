import backtrader as bt
import talib as ta
import numpy as np
import pandas as pd

class BOLL_MACD_RSI_Strategy(bt.Strategy):
    params = (
        ('boll_period', 20),        # BOLL周期
        ('boll_dev', 2),            # BOLL标准差
        ('macd1', 12),              # MACD短期周期
        ('macd2', 26),              # MACD长期周期
        ('macdsig', 9),             # MACD信号周期
        ('rsi_period', 14),         # RSI周期
        ('rsi_overbuy', 70),        # RSI超买阈值
        ('rsi_oversell', 30),       # RSI超卖阈值
        ('stop_loss', 0.03),        # 止损比例
    )

    def __init__(self):
        # 计算指标
        self.boll = bt.indicators.BollingerBands(
            self.data.close, period=self.p.boll_period, devfactor=self.p.boll_dev
        )
        self.macd = bt.indicators.MACD(
            self.data.close, period1=self.p.macd1, period2=self.p.macd2, period3=self.p.macdsig
        )
        self.rsi = bt.indicators.RSI(
            self.data.close, period=self.p.rsi_period
        )
        
        # 辅助变量：记录买入价格（用于止损）
        self.buy_price = 0

    def next(self):
        # 中轨趋势判断（当前中轨 > 前5日中轨均值，视为向上）
        boll_mid_trend_up = self.boll.mid[0] > np.mean(self.boll.mid[-5:])
        # 中轨趋势向下（当前中轨 < 前5日中轨均值）
        boll_mid_trend_down = self.boll.mid[0] < np.mean(self.boll.mid[-5:])

        # 买入信号
        if not self.position:  # 无持仓时
            # BOLL条件：价格从下轨下方回升至下轨与中轨之间
            boll_buy = (self.data.close[-1] < self.boll.low[-1]) and \
                       (self.data.close[0] > self.boll.low[0]) and \
                       (self.data.close[0] < self.boll.mid[0])
            # MACD条件：零轴下方或附近金叉，柱状线由绿转红
            macd_buy = (self.macd.macd[0] > self.macd.signal[0]) and \
                       (self.macd.macd[-1] < self.macd.signal[-1]) and \
                       (self.macd.macd[0] > -0.02)  # 允许略低于零轴
            # RSI条件：从超卖区间回升至30-50
            rsi_buy = (self.rsi[-1] < self.p.rsi_oversell) and \
                      (self.rsi[0] > self.p.rsi_oversell) and \
                      (self.rsi[0] < 50)

            if boll_buy and macd_buy and rsi_buy and boll_mid_trend_up:
                self.buy(size=100)  # 买入100股
                self.buy_price = self.data.close[0]  # 记录买入价

        # 卖出信号
        else:  # 有持仓时
            # BOLL条件：价格从上轨上方回落至上轨与中轨之间
            boll_sell = (self.data.close[-1] > self.boll.high[-1]) and \
                        (self.data.close[0] < self.boll.high[0]) and \
                        (self.data.close[0] > self.boll.mid[0])
            # MACD条件：零轴上方或附近死叉，柱状线由红转绿
            macd_sell = (self.macd.macd[0] < self.macd.signal[0]) and \
                        (self.macd.macd[-1] > self.macd.signal[-1]) and \
                        (self.macd.macd[0] < 0.02)  # 允许略高于零轴
            # RSI条件：从超买区间回落至50-70
            rsi_sell = (self.rsi[-1] > self.p.rsi_overbuy) and \
                       (self.rsi[0] < self.p.rsi_overbuy) and \
                       (self.rsi[0] > 50)

            # 止损条件：价格跌破买入价的3%
            stop_loss_condition = self.data.close[0] < self.buy_price * (1 - self.p.stop_loss)

            if (boll_sell and macd_sell and rsi_sell and boll_mid_trend_down) or stop_loss_condition:
                self.sell(size=100)  # 卖出100股


# 回测执行
if __name__ == '__main__':
    cerebro = bt.Cerebro()
    
    # 加载数据（以沪深300指数为例，需自行准备数据）
    # 数据格式：datetime, open, high, low, close, volume
    data = bt.feeds.GenericCSVData(
        dataname='000300.csv',  # 替换为你的数据文件路径
        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        dtformat='%Y-%m-%d',
        fromdate=datetime(2018, 1, 1),
        todate=datetime(2023, 1, 1)
    )
    cerebro.adddata(data)
    
    # 初始资金与佣金
    cerebro.broker.setcash(100000.0)
    cerebro.broker.setcommission(commission=0.001)  # 佣金0.1%
    
    # 添加策略
    cerebro.addstrategy(BOLL_MACD_RSI_Strategy)
    
    # 运行回测
    print('初始资金: %.2f' % cerebro.broker.getvalue())
    cerebro.run()
    print('最终资金: %.2f' % cerebro.broker.getvalue())
    
    # 绘制回测结果
    cerebro.plot()