import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

def predict_next_price(df: pd.DataFrame, minutes_ahead=10):

    if df.empty or len(df) < 10:
        return None

    df['time_idx'] = df['timestamp'].astype('int64') // 10**9
    
    X = df[['time_idx']].values
    y = df['price_usd'].values

    model = LinearRegression()
    model.fit(X, y)

    last_time = df['time_idx'].iloc[-1]
    future_times = np.array([last_time + (i * 60) for i in range(1, minutes_ahead + 1)]).reshape(-1, 1)
    
    predictions = model.predict(future_times)
    
    future_timestamps = pd.to_datetime(future_times.flatten(), unit='s')
    
    pred_df = pd.DataFrame({
        'timestamp': future_timestamps,
        'predicted_price': predictions
    })
    
    return pred_df