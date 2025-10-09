import MetaTrader5 as mt

class trade_system:




#------------------initially class trade system value------------------#
    def __init__(self,symbol,timeframe,volume,deviation,magic,sl,tp):
        self.symbol=symbol
        self.timeframe=timeframe
        self.deviation=deviation
        self.magic=magic
        self.volume=volume
        self.sl=sl
        self.tp=tp
      

#-------------make order-------------------------------------#

    def market_order(self,order_type):

        order_type_dict={
                'buy':mt.ORDER_TYPE_BUY,
                'sell': mt.ORDER_TYPE_SELL
            }
        
        price_dict={
            'buy':mt.symbol_info_tick(self.symbol).ask,
            'sell':mt.symbol_info_tick(self.symbol).bid
        }

        request={
            "action":mt.TRADE_ACTION_DEAL,
            "symbol":self.symbol,
            "volume":self.volume,
            "type":order_type_dict[order_type],
            "price":price_dict[order_type],
            "deviation":self.deviation,
            "magic":self.magic,
            'sl':self.sl,
            'tp':self.tp,
            "deviation":self.deviation,
            "comment":"python market order",
            "type_time":mt.ORDER_TIME_GTC,
            "type_filling":mt.ORDER_FILLING_IOC,
        }

        order_result=mt.order_send(request)
        return(order_result)