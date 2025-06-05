import MetaTrader5 as mt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime,timedelta
import numpy as np
import pandas_ta as ta
# from common import login,password,server
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
import asyncio
import nest_asyncio

nest_asyncio.apply()

login=51658107
password='VxBvOa*4'
server='ICMarkets-Demo'

mt.initialize()
mt.login(login,password,server)
TELEGRAM_TOKEN = '7871115076:AAGNro2Tabo0qaZrB_THvWTybr1LrNIxSR8'


# Simple Buy command
def place_order(symbol: str, volume: float, order_type: str):
    symbol = symbol.upper()
    if not mt.symbol_select(symbol, True):
        return f"❌ Symbol not found: {symbol}"

    price = mt.symbol_info_tick(symbol).ask if order_type == 'buy' else mt.symbol_info_tick(symbol).bid
    order_type_mt5 = mt.ORDER_TYPE_BUY if order_type == 'buy' else mt.ORDER_TYPE_SELL

    request = {
        "action": mt.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_mt5,
        "price": price,
        "deviation": 10,
        "magic": 123456,
        "comment": f"{order_type.capitalize()} from Telegram",
        "type_time": mt.ORDER_TIME_GTC,
        "type_filling": mt.ORDER_FILLING_IOC,
    }

    result = mt.order_send(request)
    if result.retcode == mt.TRADE_RETCODE_DONE:
        return f"✅ {order_type.capitalize()} order placed: {symbol}, {volume} lots @ {price}"
    else:
        return f"❌ Order failed: {result.retcode} — {result.comment}"

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0]
        volume = float(context.args[1])
        result = place_order(symbol, volume, 'buy')
    except (IndexError, ValueError):
        result = "⚠️ Usage: /buy SYMBOL VOLUME (e.g., /buy EURUSD 0.1)"
    await update.message.reply_text(result)


async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0]
        volume = float(context.args[1])
        result = place_order(symbol, volume, 'sell')
    except (IndexError, ValueError):
        result = "⚠️ Usage: /sell SYMBOL VOLUME (e.g., /sell EURUSD 0.1)"
    await update.message.reply_text(result)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("sell", sell_command))

    print("🤖 Bot is running with asyncio.run()...")
    await app.run_polling()

asyncio.get_event_loop().run_until_complete(main())