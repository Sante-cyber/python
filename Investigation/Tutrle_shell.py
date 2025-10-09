import numpy as np
import pandas as pd
import talib as ta
from sklearn.cluster import KMeans
import random
import MetaTrader5 as mt
from datetime import datetime,timedelta

# Generate population: Each agent represents a trading strategy with varying parameters.
def initialize_population(n_agents):
    population = []
    for _ in range(n_agents):
        # Each agent will have a random combination of trading parameters
        agent = {
            'rsi_period': random.randint(5, 20),
            'bollinger_period': random.randint(10, 30),
            'macd_fast': random.randint(5, 15),
            'macd_slow': random.randint(20, 30),
            'macd_signal': random.randint(5, 10),
        }
        population.append(agent)
    return population

# Calculate Fitness Function (FF): Evaluates the agent's performance on historical data.
def calculate_fitness(agent, data):
    # RSI
    data['RSI'] = ta.RSI(data['close'], timeperiod=agent['rsi_period'])
    # Bollinger Bands
    data['upper_band'], data['middle_band'], data['lower_band'] = ta.BBANDS(
        data['close'], timeperiod=agent['bollinger_period'])
    # MACD
    data['MACD'], data['MACD_signal'], _ = ta.MACD(data['close'], fastperiod=agent['macd_fast'],
                                                   slowperiod=agent['macd_slow'], signalperiod=agent['macd_signal'])

    # Example trading strategy: Buy when RSI < 30 and MACD crosses above signal, Sell when RSI > 70 and MACD crosses below signal
    buy_signals = (data['RSI'] < 30) & (data['MACD'] > data['MACD_signal'])
    sell_signals = (data['RSI'] > 70) & (data['MACD'] < data['MACD_signal'])

    # Simple backtest logic: Buy at buy signal, Sell at sell signal
    returns = []
    position = None
    for i in range(len(data)):
        if buy_signals.iloc[i] and position is None:
            position = data['close'].iloc[i]
        elif sell_signals.iloc[i] and position is not None:
            returns.append(data['close'].iloc[i] - position)
            position = None
    # Calculate fitness as total profit or return
    total_profit = sum(returns)
    return total_profit

# Initial clustering: Use vertical clustering to group agents by fitness levels.
def vertical_clustering(population, data):
    fitness_scores = [calculate_fitness(agent, data) for agent in population]
    return fitness_scores

# Horizontal K-means clustering: Group agents by similarities in parameters.
def horizontal_clustering(population, n_clusters=5):
    # Prepare data for clustering
    param_values = np.array([[agent['rsi_period'], agent['bollinger_period'], agent['macd_fast'],
                              agent['macd_slow'], agent['macd_signal']] for agent in population])
    kmeans = KMeans(n_clusters=n_clusters)
    clusters = kmeans.fit_predict(param_values)
    return clusters

# TSEA process: Apply evolution and growth algorithm to optimize trading signals.
def turtle_shell_evolution(population, data, epochs=100, cluster_epochs=50):
    for epoch in range(epochs):
        # 1. Calculate fitness and cluster population vertically
        fitness_scores = vertical_clustering(population, data)
        population_clusters = horizontal_clustering(population)
        
        # 2. Evolution step: Replace worst solutions, expand clusters outward
        for i, agent in enumerate(population):
            if random.random() < 0.8:  # 80% chance of using the best solution in a cluster
                cluster_agents = [population[j] for j in range(len(population)) if population_clusters[j] == population_clusters[i]]
                best_agent = max(cluster_agents, key=lambda x: calculate_fitness(x, data))
                new_agent = mutate_agent(best_agent)  # Mutate agent slightly
                if calculate_fitness(new_agent, data) > fitness_scores[i]:
                    population[i] = new_agent  # Replace agent if new one is better
        
        # 3. Every 50 epochs, re-cluster population vertically and horizontally
        if epoch % cluster_epochs == 0:
            population_clusters = horizontal_clustering(population)
    
    # After evolution, return the best-performing agent
    best_agent = max(population, key=lambda x: calculate_fitness(x, data))
    return best_agent

# Mutation function to create variations in agents
def mutate_agent(agent):
    new_agent = agent.copy()
    new_agent['rsi_period'] = min(max(new_agent['rsi_period'] + random.randint(-2, 2), 5), 20)
    new_agent['bollinger_period'] = min(max(new_agent['bollinger_period'] + random.randint(-5, 5), 10), 30)
    new_agent['macd_fast'] = min(max(new_agent['macd_fast'] + random.randint(-2, 2), 5), 15)
    new_agent['macd_slow'] = min(max(new_agent['macd_slow'] + random.randint(-2, 2), 20), 30)
    new_agent['macd_signal'] = min(max(new_agent['macd_signal'] + random.randint(-1, 1), 5), 10)
    return new_agent

# Example usage
if __name__ == "__main__":
    login=51658107
    password='VxBvOa*4'
    server='ICMarkets-Demo'

    mt.initialize()
    mt.login(login,password,server)
    # Load market data (for example, you can use a CSV file with OHLCV data)
    
    symbol=['GBPAUD']
    bars=mt.copy_rates_range('GBPAUD',mt.TIMEFRAME_H4,datetime(2023,1,1), datetime(2023,12,31))
    df=pd.DataFrame(bars)
    df['time']=pd.to_datetime(df['time'],unit='s')
    df['hour']=df['time'].dt.hour

    data=df
    # Initialize population of agents
    population_size = 100
    population = initialize_population(population_size)

    # Run TSEA optimization for trading signals
    best_agent = turtle_shell_evolution(population, df)

    # Best agent's optimized parameters
    print("Best agent parameters:", best_agent)
