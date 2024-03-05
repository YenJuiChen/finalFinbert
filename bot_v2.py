import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime
import ast

# 初始化MT5連接的函數
def init_mt5():
    if not mt5.initialize():
        print("Initialize() failed, error code =", mt5.last_error())
        mt5.shutdown()
        quit()

class MLTraderMT5:
    def __init__(self, symbol="EURUSD", cash_at_risk=0.5):
        self.symbol = symbol
        self.cash_at_risk = cash_at_risk
        self.last_trade_time = None
        self.trade_interval = pd.Timedelta(hours=1)  # 控制交易間隔為1小時

    def get_cash(self):
        account_info = mt5.account_info()
        if account_info is None:
            print("Failed to get account info", mt5.last_error())
            return None
        else:
            return account_info.balance

    def get_last_price(self, symbol):
        price = mt5.symbol_info_tick(symbol).ask
        return price

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        if last_price <= 0:  # 检查last_price是否有效
            print(f"Invalid last price for {self.symbol}. Skipping trade.")
            return None, None, None  # 返回None表示无法进行交易
        quantity = round(cash * self.cash_at_risk / last_price, 0)   #下單量計算
        return cash, last_price, quantity
    def get_sentiment(self):
        try:
            df = pd.read_csv("news_analysis_results.csv", header=None)
            analysis_result_str = df.iloc[1, 2]
            try:
                analysis_results = ast.literal_eval(analysis_result_str)
                # 打印分析结果，检查结构
                print("分析结果结构:", analysis_results)
                # 根据打印出的结构调整下面的索引
                sentiment = analysis_results[0][0][0]['label']
                score = analysis_results[0][0][0]['score']
                return score, sentiment
            except ValueError as e:
                print("解析失败的字符串:", analysis_result_str)
                print("解析错误:", str(e))
                return 0, "neutral"
        except FileNotFoundError:
            print("Sentiment analysis results file not found.")
            return 0, "neutral"
    
    def create_order(self, symbol, quantity, order_type, price=None):
        # 根据当前市场价格动态计算止损和止盈
        point = mt5.symbol_info(symbol).point
        if order_type == "buy":
            price = mt5.symbol_info_tick(symbol).ask
            sl = price - 1000 * point  # 止損價
            tp = price + 1000 * point  # 止盈價
        elif order_type == "sell":
            price = mt5.symbol_info_tick(symbol).bid
            sl = None # 止損價
            tp = None # 止盈價
        else:
            raise Exception('Order type must be either "buy" or "sell".')
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": 0.01,   #下單量先修改
            "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 200,
            "magic": 234000,
            "comment": "sent by script",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        # 在发送请求之前，移除SL和TP键（如果它们为None）
        if sl is None:
           del request['sl']
        if tp is None:
           del request['tp']

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Order send failed, retcode = {result.retcode}")
        else:
            print(f"Order executed successfully, {result}")
            self.last_trade_time = datetime.now()
    
    def execute_strategy(self):
        cash, last_price, quantity = self.position_sizing()
        if last_price is None:  # 检查是否获取到有效的last_price
            return  # 如果last_price无效，则直接返回不执行后续操作
        probability, sentiment = self.get_sentiment()

        # 如果情緒為neutral或概率不足，則不執行操作
        if sentiment == "neutral":
            print("Neutral sentiment detected, no action taken.")
            return
        
        # 根据新的交易条件进行决策
        if sentiment == "positive" and probability > 0.70:
            print(f"Positive sentiment detected with high confidence ({probability}), executing buy order.")
            self.create_order(self.symbol, quantity, "buy")
        elif sentiment == "negative" and probability > 0.70:
            print(f"Negative sentiment detected with high confidence ({probability}), executing sell order.")
            self.create_order(self.symbol, quantity, "sell")
        else:
            print(f"No action taken. Sentiment: {sentiment}, Probability: {probability}")
        
if __name__ == "__main__":
    while True:
        init_mt5()
        trader = MLTraderMT5(symbol="EURUSD", cash_at_risk=0.5)
        trader.execute_strategy()
        mt5.shutdown()

        print(f"Strategy executed at {datetime.now()}. Waiting for next interval...")
        time.sleep(3600)  # 暫停一小時後再次執行
