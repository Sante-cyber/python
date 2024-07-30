import pandas as pd
import numpy as np
from datetime import datetime
import MetaTrader5 as mt
import pandas_ta as ta
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE
from lightgbm import LGBMClassifier

# Initialize and login to MetaTrader 5
login = 51658107
password = 'VxBvOa*4'
server = 'ICMarkets-Demo'
mt.initialize()
mt.login(login, password, server)

# Fetch historical data
symbol = 'EURJPY'
bars = mt.copy_rates_range(symbol, mt.TIMEFRAME_M30, datetime(2020, 1, 1), datetime(2024, 12, 31))
df = pd.DataFrame(bars)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Calculate technical indicators
df['rsi'] = ta.rsi(df['close'], length=14)
df['ma'] = df['close'].rolling(window=14).mean()
macd = ta.macd(df['close'])
df['macd'] = macd['MACD_12_26_9']
df['macd_signal'] = ta.macd(df['close'])['MACDs_12_26_9']
df['macd_histogram'] = ta.macd(df['close'])['MACDh_12_26_9']

df['volume_ma_10'] = df['tick_volume'].rolling(window=10).mean()
df['volume_ma_20'] = df['tick_volume'].rolling(window=20).mean()
df['volume_change_lag1'] = df['tick_volume'].pct_change().shift(1)

df['ema_20'] = ta.ema(df['close'], length=20)
df['ema_50'] = ta.ema(df['close'], length=50)



# Calculate Bollinger Bands and assign the appropriate columns
bollinger_bands = ta.bbands(df['close'], length=20, std=2.0)
df['bollinger_upper'] = bollinger_bands['BBU_20_2.0']
df['bollinger_lower'] = bollinger_bands['BBL_20_2.0']

stoch = ta.stoch(df['high'], df['low'], df['close'])
df['stoch_k'] = stoch['STOCHk_14_3_3']
df['stoch_d'] = stoch['STOCHd_14_3_3']

df['atr'] = ta.atr(df['high'], df['low'], df['close'])


df['doji'] = np.where((abs(df['open'] - df['close']) / (df['high'] - df['low']) < 0.1), 1, 0)
df['rolling_mean'] = df['close'].rolling(window=14).mean()
df['rolling_std'] = df['close'].rolling(window=14).std()



# Create time-based features
df['hour'] = df['time'].dt.hour
df['day_of_week'] = df['time'].dt.dayofweek
df['month'] = df['time'].dt.month


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


# Create the target variable
df['target_rsi'] = df['rsi'].shift(-1)
df['target'] = (df['target_rsi'] > 70).astype(int)


df.dropna(inplace=True)
df.reset_index(drop=True, inplace=True)


# Define features and target
features = [
    'rsi_lag1', 'bollinger_upper_lag1',  'volume_lag1', 'hour', 'day_of_week', 'month', 'doji_lag','macd_histogram_lag1'
]
target = 'target'

# Split the data into training and testing sets
X = df[features]
y = df[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)


X_test_index = X_test.index

# Handle class imbalance
smote = SMOTE()
X_train, y_train = smote.fit_resample(X_train, y_train)

# Standardize features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Train a LightGBM model with Grid Search
param_grid = {
   'n_estimators': [300],
    'max_depth': [10],
    'learning_rate': [0.01],
    'num_leaves': [31],
    'min_child_samples': [50]
}

model = LGBMClassifier()
grid_search = GridSearchCV(model, param_grid, cv=StratifiedKFold(n_splits=5), scoring='f1', n_jobs=-1)
grid_search.fit(X_train, y_train)


print('Best parameters found: ', grid_search.best_params_)
best_model = grid_search.best_estimator_

# Evaluate the best model
y_pred_best = best_model.predict(X_test)
print(classification_report(y_test, y_pred_best))

# Feature importance
import matplotlib.pyplot as plt
import seaborn as sns

feature_importances = pd.DataFrame({
    'feature': features,
    'importance': best_model.feature_importances_
})
feature_importances = feature_importances.sort_values(by='importance', ascending=False)


# Calculate cumulative importance
feature_importances['cumulative_importance'] = feature_importances['importance'].cumsum() / feature_importances['importance'].sum()

# Display the top features contributing to 95% of importance
top_features = feature_importances[feature_importances['cumulative_importance'] <= 0.95]
print(top_features)


plt.figure(figsize=(10, 6))
sns.barplot(x='importance', y='feature', data=feature_importances)
plt.title('Feature Importances')
plt.show()
