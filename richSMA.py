import MetaTrader5 as mt5
import datetime
from time import sleep

# 登入MT5平台
def init_mt5():
    if not mt5.initialize(login=5023253958, password="*sYgVr6w", server="MetaQuotes-Demo"):
        print("Initialize() failed, error code =", mt5.last_error())
        mt5.shutdown()
        quit()
    else:
        print("MT5 initialized successfully")

# 計算EMA
def calculate_ema(symbol, period, price_type, bars_number):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, bars_number)
    ema_values = []
    multiplier = 2 / (period + 1)
    print(symbol, period, price_type, bars_number)

    if rates is not None and len(rates) > 0:
        # 使用字符串键访问对应的价格类型，如'close'代替mt5.PRICE_CLOSE
        initial_sma = sum(rate[price_type] for rate in rates[:period]) / period
        ema_values.append(initial_sma)
        
        for i in range(period, len(rates)):
            ema = (rates[i][price_type] - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)
    print(ema_values)        
    return ema_values

# 初始化
def init(symbol, magic):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 1)
    bars = rates.size if rates is not None else 0
    point = mt5.symbol_info(symbol).point
    print(f"Number of bars: {bars}, Point size: {point}")
    return bars, point

# 檢查有無買單
def check_buy_orders(symbol, magic):
    buy_orders = mt5.positions_get(symbol=symbol, group="YOUR_GROUP")
    buy_total = sum(1 for order in buy_orders if order.magic == magic and order.type == mt5.ORDER_TYPE_BUY)
    print(f"Number of buy orders: {buy_total}")
    return buy_total

# 檢查有無賣單 
def check_sell_orders(symbol, magic):
    sell_orders = mt5.positions_get(symbol=symbol, group="YOUR_GROUP")
    sell_total = sum(1 for order in sell_orders if order.magic == magic and order.type == mt5.ORDER_TYPE_SELL)
    print(f"Number of sell orders: {sell_total}")
    return sell_total

# 買入規則
def buy_rule(symbol, timeframe):
    ema_fast = calculate_ema(symbol, 5, 'close', 10)
    ema_slow = calculate_ema(symbol, 20, 'close', 42)
    
    if len(ema_fast) > 1 and len(ema_slow) > 1:
        if ema_fast[-1] > ema_slow[-1] and ema_fast[-2] <= ema_slow[-2]:
            print("Buy signal triggered")
            return True
        
    return False

# 賣出規則
def sell_rule(symbol, timeframe):
    ema_fast = calculate_ema(symbol, 5, 'close', 10)
    ema_slow = calculate_ema(symbol, 20, 'close', 42)
    
    if len(ema_fast) > 1 and len(ema_slow) > 1:
        if ema_fast[-1] < ema_slow[-1] and ema_fast[-2] > ema_slow[-2]:
            print("Sell signal triggered")
            return True
        
    return False

# 設置買單止損止盈
def set_buy_sl_tp(symbol, magic, stop_loss_points, take_profit_points):
    buy_orders = mt5.positions_get(symbol=symbol, group="YOUR_GROUP")
    for order in buy_orders:
        if order.magic == magic and order.type == mt5.ORDER_TYPE_BUY:
            if stop_loss_points > 0:
                sl = order.price_open - stop_loss_points * mt5.symbol_info(symbol).point
            else:
                sl = order.sl
            
            if take_profit_points > 0:
                tp = order.price_open + take_profit_points * mt5.symbol_info(symbol).point
            else:
                tp = order.tp
                
            result = mt5.order_modify(order.ticket, order.price_open, sl, tp)
            if result:
                print(f"Buy order #{order.ticket} SL/TP modified successfully")
            else:
                print(f"Failed to modify buy order #{order.ticket} SL/TP, error code: {mt5.last_error()}")

# 設置賣單止損止盈 
def set_sell_sl_tp(symbol, magic, stop_loss_points, take_profit_points):
    sell_orders = mt5.positions_get(symbol=symbol, group="YOUR_GROUP")
    for order in sell_orders:
        if order.magic == magic and order.type == mt5.ORDER_TYPE_SELL:
            if stop_loss_points > 0:
                sl = order.price_open + stop_loss_points * mt5.symbol_info(symbol).point
            else:
                sl = order.sl
                
            if take_profit_points > 0:
                tp = order.price_open - take_profit_points * mt5.symbol_info(symbol).point
            else:
                tp = order.tp
                
            result = mt5.order_modify(order.ticket, order.price_open, sl, tp)
            if result:
                print(f"Sell order #{order.ticket} SL/TP modified successfully")
            else:
                print(f"Failed to modify sell order #{order.ticket} SL/TP, error code: {mt5.last_error()}")
    
# 平倉買單
def close_buy(symbol, magic):
    buy_orders = mt5.positions_get(symbol=symbol, group="YOUR_GROUP")
    for order in buy_orders:
        if order.magic == magic and order.type == mt5.ORDER_TYPE_BUY:
            result = mt5.order_close(order.ticket)
            if result:
                print(f"Buy order #{order.ticket} closed successfully")
            else:
                print(f"Failed to close buy order #{order.ticket}, error code: {mt5.last_error()}")
        
# 平倉賣單
def close_sell(symbol, magic):
    sell_orders = mt5.positions_get(symbol=symbol, group="YOUR_GROUP")
    for order in sell_orders:
        if order.magic == magic and order.type == mt5.ORDER_TYPE_SELL:
            result = mt5.order_close(order.ticket)
            if result:
                print(f"Sell order #{order.ticket} closed successfully")
            else:
                print(f"Failed to close sell order #{order.ticket}, error code: {mt5.last_error()}")
            
def main():
    # 登入MT5
    init_mt5()
    
    # 參數設置
    symbol = "XAUUSD"
    magic = 123456
    lot_size = 0.1
    stop_loss_points = 0  # 0表示不設置止損
    take_profit_points = 0  # 0表示不設置止盈
    # max_run_time = datetime.datetime(2020, 12, 31, 23, 59, 59)  # 設置最大運行時間

    # 初始化    
    bars, point = init(symbol, magic)
    
    while True:
        # 檢查是否有單
        buy_total = check_buy_orders(symbol, magic)
        sell_total = check_sell_orders(symbol, magic)
        
        # 有買單,檢查是否出場
        if buy_total > 0:
            if sell_rule(symbol, mt5.TIMEFRAME_M5):
                close_buy(symbol, magic)
        
        # 有賣單,檢查是否出場
        elif sell_total > 0:
            if buy_rule(symbol, mt5.TIMEFRAME_M5):
                close_sell(symbol, magic)
        
        # 沒有單,檢查是否可開倉
        else:
            # 買入
            if buy_rule(symbol, mt5.TIMEFRAME_M5):
                buy = mt5.order_send_buy(symbol=symbol, lot=lot_size, magic=magic)
                if buy.exec_type != mt5.TRADE_RETCODE_REJECTED:
                    print(f"Buy order #{buy.order} opened successfully")
                    set_buy_sl_tp(symbol, magic, stop_loss_points, take_profit_points)
                else:
                    print(f"Failed to open buy order, error code: {mt5.last_error()}")
            
            # 賣出 
            elif sell_rule(symbol, mt5.TIMEFRAME_M5):
                sell = mt5.order_send_sell(symbol=symbol, lot=lot_size, magic=magic)
                if sell.exec_type != mt5.TRADE_RETCODE_REJECTED:
                    print(f"Sell order #{sell.order} opened successfully")
                    set_sell_sl_tp(symbol, magic, stop_loss_points, take_profit_points)
                else:
                    print(f"Failed to open sell order, error code: {mt5.last_error()}")
        
        sleep(1)  # 避免CPU佔用率過高

if __name__ == "__main__":
    main()