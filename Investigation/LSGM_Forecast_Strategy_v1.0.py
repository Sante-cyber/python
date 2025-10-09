import pandas as pd
import numpy as np
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
import MetaTrader5 as mt
import pandas_ta as ta
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold,RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report,roc_auc_score,make_scorer, f1_score
from imblearn.over_sampling import SMOTE
from lightgbm import LGBMClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

# Initialize and login to MetaTrader 5
login = 51658107
password = 'VxBvOa*4'
server = 'ICMarkets-Demo'
mt.initialize()
mt.login(login, password, server)


def get_forecast_month_list(start_date):


    # Create a list to store the formatted dates
    formatted_dates = []

    # Loop through each month from January to December 2023
    for i in range(43):
        # Compute the date for the current month
        current_date = start_date + relativedelta(months=i)
        # Format the date as `datetime(YYYY, MM, DD)`
        # Append the formatted date to the list
        formatted_dates.append(current_date)
    return formatted_dates

def rsi(data,window):
    data['rsi']=ta.rsi(data.close, length=window)
    data['overbought']=70
    data['oversold']=30
    return data




forecast_month_list=get_forecast_month_list(datetime(2024, 1, 1))   

best_param_total=pd.DataFrame()
report_df=pd.DataFrame()
df_forecast=pd.DataFrame()

for i in forecast_month_list:
    test_start_date=i
    # Calculate the first day of the previous 12 months
    train_start_date = test_start_date - relativedelta(months=12)
    train_end_date=test_start_date- timedelta(days=1)
    # Calculate the last day of the current month
    test_end_date = test_start_date + relativedelta(months=1) - timedelta(days=1)



    

    # Fetch historical data
    symbol = 'EURJPY'
    bars = mt.copy_rates_range(symbol, mt.TIMEFRAME_M30, train_start_date, test_end_date)
    df = pd.DataFrame(bars)
    df['time'] = pd.to_datetime(df['time'], unit='s')


    # Calculate technical indicators
    df=rsi(df,17)
    df['ma'] = df['close'].rolling(window=14).mean()
    macd = ta.macd(df['close'])
    df['macd'] = macd['MACD_12_26_9']
    df['macd_signal'] = macd['MACDs_12_26_9']
    df['macd_histogram'] = macd['MACDh_12_26_9']
    df['atr'] = ta.atr(df['high'], df['low'], df['close'])
 
    # Additional features
    df['volume_ma_10'] = df['tick_volume'].rolling(window=10).mean()
    df['volume_ma_20'] = df['tick_volume'].rolling(window=20).mean()
    df['volume_change_lag1'] = df['tick_volume'].pct_change().shift(1)
    df['ema_20'] = ta.ema(df['close'], length=20)
    df['ema_50'] = ta.ema(df['close'], length=50)



    # Calculate Bollinger Bands and assign the appropriate columns
    bollinger_bands = ta.bbands(df['close'], length=20, std=2.0)
    df['bollinger_upper'] = bollinger_bands['BBU_20_2.0']
    df['bollinger_lower'] = bollinger_bands['BBL_20_2.0']

    # Stochastic Oscillator
    stoch = ta.stoch(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch['STOCHk_14_3_3']
    df['stoch_d'] = stoch['STOCHd_14_3_3']



    # Candle patterns and statistical features
    df['doji'] = np.where((abs(df['open'] - df['close']) / (df['high'] - df['low']) < 0.1), 1, 0)
    df['rolling_mean'] = df['close'].rolling(window=14).mean()
    df['rolling_std'] = df['close'].rolling(window=14).std()



    # Time-based features
    df['hour'] = df['time'].dt.hour
    df['day_of_week'] = df['time'].dt.dayofweek
    df['month'] = df['time'].dt.month
    df['date'] = df['time'].dt.date

    # Lagged Features
    df['rsi_lag1'] = df['rsi'].shift(1)
    df['rsi_lag2'] = df['rsi'].shift(2)
    df['rsi_lag3'] = df['rsi'].shift(3)
    df['ma_lag1'] = df['ma'].shift(1)
    df['macd_lag1'] = df['macd'].shift(1)
    df['macd_signal_lag1'] = df['macd_signal'].shift(1)
    df['macd_histogram_lag1'] = df['macd_histogram'].shift(1)
    df['bollinger_upper_lag1'] = df['bollinger_upper'].shift(1)
    df['bollinger_lower_lag1'] = df['bollinger_lower'].shift(1)
    df['stoch_k_lag1'] = df['stoch_k'].shift(1)
    df['stoch_d_lag1'] = df['stoch_d'].shift(1)
    df['atr_lag1'] = df['atr'].shift(1)
    df['volume_lag1'] = df['tick_volume'].shift(1)
    df['volume_lag2'] = df['tick_volume'].shift(2)
    df['volume_change_lag_lag'] = df['volume_change_lag1'].shift(1)
    df['rolling_mean_lag'] = df['rolling_mean'].shift(1)
    df['rolling_std_lag'] = df['rolling_std'].shift(1)
    df['doji_lag'] = df['doji'].shift(1)
    df['ema_20_lag'] = df['ema_20'].shift(1)
    df['ema_50_lag'] = df['ema_50'].shift(1)
    
    # Interaction Features
    df['rsi_macd_interaction'] = df['rsi_lag1'] * df['macd_histogram_lag1']
    df['price_volume_interaction'] = df['close'] * df['tick_volume']


    df['signal'] = np.where(
        (df['high'] - df['open'] > 0) & (df['close'] - df['open'] > 0) & (df['low'] == df['open']), 0,
        np.where(
            (df['high'] - df['open'] > 0) & (df['close'] - df['open'] > 0) & (df['low'] - df['open'] < 0), 1,
            np.where(
                (df['high'] - df['open'] > 0) & (df['close'] - df['open'] < 0) & (df['low'] - df['open'] < 0), -1,
                np.where(
                    (df['high'] == df['open']) & (df['close'] - df['open'] < 0) & (df['low'] - df['open'] < 0), 0,
                    0
                )
            )
        )
    )
    
    # Create the target variable
    df['target_signal'] = df['signal'].shift(-1)


    df.dropna(inplace=True)
    df.reset_index(drop=True, inplace=True)

    df['target_signal']=df['target_signal'].astype(int)
    # Define features and target
    
    features = [
    'price_volume_interaction',
    'tick_volume',
    'volume_change_lag_lag',
    'volume_lag1',
    'month',
    'rolling_std_lag',
    'hour',
    'volume_lag2',
    'volume_ma_20',
    'atr',
    'stoch_k',
    'doji_lag',
    'volume_ma_10',
    'day_of_week',
    'rsi_macd_interaction',
    'macd_signal_lag1',
    'rsi',
    'atr_lag1',
    'rsi_lag3',
    'stoch_d_lag1',
    'macd_histogram_lag1',
    'rsi_lag2',
    'rsi_lag1',
    'stoch_k_lag1',
    'bollinger_upper',
    'macd',
    'bollinger_lower',
    'ema_50',
    'macd_lag1',
    'ema_50_lag',
    'bollinger_upper_lag1',
    'bollinger_lower_lag1',
    'stoch_d',
    'doji',
    'ema_20',
    'ma',
    'ma_lag1',
    'ema_20_lag',
    'rolling_mean_lag',
    'rolling_mean',
    ]
    # features = [
    # 'rsi','rsi_lag1', 'rsi_lag2', 'rsi_lag3',
    # 'macd','macd_histogram_lag1', 'macd_lag1', 'macd_signal_lag1',
    # 'bollinger_upper','bollinger_upper_lag1','bollinger_lower','bollinger_lower_lag1',
    # 'volume_ma_10','volume_ma_20','tick_volume','volume_lag1', 'volume_lag2', 'volume_change_lag_lag',
    # 'ema_20','ema_20_lag', 'ema_50','ema_50_lag',
    # 'stoch_k','stoch_k_lag1', 'stoch_d','stoch_d_lag1',
    # 'atr','atr_lag1',
    # 'ma','ma_lag1',
    # 'rolling_mean','rolling_mean_lag', 'rolling_std_lag',
    # 'doji','doji_lag',
    # 'hour', 'day_of_week', 'month',
    # 'rsi_macd_interaction', 'price_volume_interaction'
    # ]
    target = 'target_signal'


    train_data = df[(df['time'] >= train_start_date) & (df['time'] <= train_end_date)]
    test_data = df[(df['time'] >= test_start_date) & (df['time'] <= test_end_date)]
    
    X_train = train_data[features]
    y_train = train_data[target]
    X_test = test_data[features]
    y_test = test_data[target]


    X_test_index = X_test.index

    # Handle class imbalance
    smote = SMOTE()
    X_train, y_train = smote.fit_resample(X_train, y_train)

    # Standardize features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    
    f1_macro = make_scorer(f1_score, average='macro')

    # Train a LightGBM model with Grid Search
    param_grid = {
     'n_estimators': [100, 200, 300],
     'max_depth': [10, 20, 30],
     'learning_rate': [0.01, 0.05, 0.1],
     'num_leaves': [31, 50, 70],
     'min_child_samples': [20, 30, 50]
    }



    model = LGBMClassifier(force_col_wise=True)
    grid_search = RandomizedSearchCV(model, param_grid, cv=StratifiedKFold(n_splits=5), 
                                 scoring=f1_macro, n_jobs=-1, verbose=1)
    grid_search.fit(X_train, y_train)


    print('Best parameters found: ', grid_search.best_params_)
    best_param=grid_search.best_params_
    forcast_month=test_start_date.strftime('%Y-%m')
    best_param['month']=forcast_month
    best_param_df = pd.DataFrame([best_param])
    best_param_total = pd.concat([best_param_total, best_param_df], ignore_index=True)
    best_model = grid_search.best_estimator_
    
    model_path=f'C:/c/EA/LSGM Model/best_model_LSGM_{forcast_month}.pkl'
    with open(model_path, 'wb') as file:
        pickle.dump(best_model, file)
    
    # Evaluate the best model
    y_pred_best = best_model.predict(X_test)
    report = classification_report(y_test, y_pred_best, output_dict=True)
    report_df_temp = pd.DataFrame(report).transpose()
    report_df_temp['month']=forcast_month
    print(report_df_temp)
    report_df_temp=report_df_temp.reset_index()
    report_df=pd.concat([report_df,report_df_temp],ignore_index=True)
    
    
    df_test = df.iloc[X_test_index]
    df_test['predicted_target'] = y_pred_best
    df_forecast=pd.concat([df_forecast,df_test],ignore_index=True)
    
    
    feature_importances_temp = pd.DataFrame({
        'feature': features,
        'importance': best_model.feature_importances_
    })
    feature_importances_temp = feature_importances_temp.sort_values(by='importance', ascending=False)
    feature_importances_temp['month']=forcast_month
    feature_importances_temp['cumulative_importance'] = feature_importances_temp['importance'].cumsum() / feature_importances_temp['importance'].sum()
    top_features = feature_importances_temp[feature_importances_temp['cumulative_importance'] <= 0.95]
    feature_importances=pd.concat([feature_importances_temp,top_features],ignore_index=True)


best_param_total.to_csv('C:/c/EA/LSGM Model/best_param.csv')
df_forecast.to_csv('C:/c/EA/LSGM Model/forecast_result.csv')
report_df.to_csv('C:/c/EA/LSGM Model/model_test.csv')
feature_importances.to_csv('C:/c/EA/LSGM Model/model_feature_importance1.csv')


    # feature_importances = pd.DataFrame({
    #     'feature': features,
    #     'importance': best_model.feature_importances_
    # })
    # feature_importances = feature_importances.sort_values(by='importance', ascending=False)
    
    
    # # Calculate ROC-AUC score
    # roc_auc = roc_auc_score(y_test, best_model.predict_proba(X_test)[:, 1])

    # print(f"Month: {forcast_month}")
    # print(f"ROC-AUC: {roc_auc:.4f}")
    # print(report_df)


    # # Calculate cumulative importance
    # feature_importances['cumulative_importance'] = feature_importances['importance'].cumsum() / feature_importances['importance'].sum()

    # # Display the top features contributing to 95% of importance
    # top_features = feature_importances[feature_importances['cumulative_importance'] <= 0.95]
    # top_features = top_features['feature'].tolist()


    # plt.figure(figsize=(10, 6))
    # sns.barplot(x='importance', y='feature', data=feature_importances)
    # plt.title('Feature Importances')
    # plt.show()
