import pandas as pd
import numpy as np
from datetime import datetime
import MetaTrader5 as mt
import pandas_ta as ta
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV

# Initialize and login to MetaTrader 5
login = 51658107
password = 'VxBvOa*4'
server = 'ICMarkets-Demo'
mt.initialize()
mt.login(login, password, server)

# Fetch historical data
symbol = 'EURJPY'
bars = mt.copy_rates_range(symbol, mt.TIMEFRAME_M30, datetime(2021, 1, 1), datetime(2021, 12, 31))
df = pd.DataFrame(bars)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Calculate RSI
df['rsi'] = ta.rsi(df['close'], length=14)

# Create the target variable
df['target_rsi'] = df['rsi'].shift(-1)
df['target'] = (df['target_rsi'] > 70).astype(int)
df['rsi_lag1'] = df['rsi'].shift(1)
df['rsi_lag2'] = df['rsi'].shift(2)
df['ma'] = df['close'].rolling(window=14).mean()
df['ma_lag1'] = df['ma'].shift(1)

# Drop NaN values created by lagging and target shifting
df.dropna(inplace=True)

df.reset_index(drop=True, inplace=True)
# Define features and target
features = ['rsi_lag1', 'rsi_lag2', 'ma_lag1']
target = 'target'

# Split the data into training and testing sets
X = df[features]
y = df[target]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)


X_test_index = X_test.index

# Standardize features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Train a Logistic Regression model
model = LogisticRegression()
model.fit(X_train, y_train)


# Predict the target values
y_pred = model.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy}')
print(classification_report(y_test, y_pred))

# Identify when the RSI is forecasted to be greater than 70
df_test = df.iloc[X_test_index]
df_test['predicted_target'] = y_pred
overbought_signals = df_test[df_test['predicted_target'] == 1]
print('Overbought signals:')
print(overbought_signals[['time', 'predicted_target']])

df_test.to_csv('C:/Ally/a.csv')

# Define parameter grid
param_grid = {
    'C': [0.01, 0.1, 1, 10, 100],
    'penalty': ['l1', 'l2'],
    'solver': ['liblinear']
}

# Grid search
grid_search = GridSearchCV(LogisticRegression(), param_grid, cv=5, scoring='accuracy')
grid_search.fit(X_train, y_train)

# Best parameters
print('Best parameters found: ', grid_search.best_params_)
best_model = grid_search.best_estimator_

# Evaluate the best model
y_pred_best = best_model.predict(X_test)
accuracy_best = accuracy_score(y_test, y_pred_best)
print(f'Optimized Accuracy: {accuracy_best}')
print(classification_report(y_test, y_pred_best))


