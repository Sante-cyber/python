import MetaTrader5 as mt

class trade_set:
#------------------initially class attribute value------------------#
    def __init__(self,open_datetime,open_price,order_type,volume,sl,tp,symbol):
        self.order_type=order_type
        self.volume=volume
        self.sl=sl
        self.tp=tp
        self.close_datetime=None
        self.close_price=None
        self.profit=None
        self.status='open'
        self.symbol=symbol

#-------------make order-------------------------------------#

    def market_order(symbol,volume,order_type,deviation,magic,stoploss,takeprofit):

        order_type_dict={
                'buy':mt.ORDER_TYPE_BUY,
                'sell': mt.ORDER_TYPE_SELL
            }
        
        price_dict={
            'buy':mt.symbol_info_tick(symbol).ask,
            'sell':mt.symbol_info_tick(symbol).bid
        }

        request={
            "action":mt.TRADE_ACTION_DEAL,
            "symbol":symbol,
            "volume":volume,
            "type":order_type_dict[order_type],
            "price":price_dict[order_type],
            "deviation":deviation,
            "magic":magic,
            'sl':stoploss,
            'tp':takeprofit,
            "deviation":deviation,
            "comment":"python market order",
            "type_time":mt.ORDER_TIME_GTC,
            "type_filling":mt.ORDER_FILLING_IOC,
        }

        order_result=mt.order_send(request)
        return(order_result)