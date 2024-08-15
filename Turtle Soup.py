import MetaTrader5 as mt
import pandas as pd
from datetime import datetime, timedelta
from common import login,password,server

if mt.initialize():
    print('connect to MetaTrader5')
    mt.login(login,password,server)
    # mt.login(login,password,server)

