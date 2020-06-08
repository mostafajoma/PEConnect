import numpy as np
import pandas as pd
import hvplot.pandas


from numpy.random import seed
seed(1)
from tensorflow import random
random.set_seed(2)


df = pd.read_csv('../LSTM_Predictions/spxreturns.csv',index_col="Date", infer_datetime_format=True, parse_dates=True)
df2 = pd.read_csv('../LSTM_Predictions/spxreturns2.csv', index_col="Date", infer_datetime_format=True, parse_dates=True)
df = df.join(df2, how="inner")



def window_data(df, window, feature_col_number, target_col_number):
    X = []
    y = []
    for i in range(len(df) - window - 1):
        features = df.iloc[i:(i + window), feature_col_number]
        target = df.iloc[(i + window), target_col_number]
        X.append(features)
        y.append(target)
    return np.array(X), np.array(y).reshape(-1, 1)



window_size = 1
feature_column = 1
target_column = 1

X, y = window_data(df, window_size, feature_column, target_column)

#print (f"X sample values:\n{X[:1]} \n")
#print (f"y sample values:\n{y[:5]}")


split = int(0.7 * len(X))
X_train = X[: split - 1]
X_test = X[split:]
y_train = y[: split - 1]
y_test = y[split:]


from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
scaler.fit(X)
X_train = scaler.transform(X_train)
X_test = scaler.transform(X_test)
scaler.fit(y)
y_train = scaler.transform(y_train)
y_test = scaler.transform(y_test)


X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

#print (f"X_train sample values:\n{X_train[:2]} \n")
#print (f"X_test sample values:\n{X_test[:2]}")




from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout





model = Sequential()

number_units = 30
dropout_fraction = 0.2

# Layer 1
model.add(LSTM(
    units=number_units,
    return_sequences=True,
    input_shape=(X_train.shape[1], 1))
    )
model.add(Dropout(dropout_fraction))

# Layer 2
model.add(LSTM(units=number_units, return_sequences=True))
model.add(Dropout(dropout_fraction))

# Layer 3
model.add(LSTM(units=number_units))
model.add(Dropout(dropout_fraction))

# Output layer
model.add(Dense(1))



model.compile(optimizer="adam", loss="mean_squared_error")

#model.summary()

model.fit(X_train, y_train, epochs=10, shuffle=False, batch_size=1, verbose=0)

#model.evaluate(X_test, y_test)

predicted = model.predict(X_test)

predicted_prices = scaler.inverse_transform(predicted)
real_prices = scaler.inverse_transform(y_test.reshape(-1, 1))


stocks = pd.DataFrame({
    "Real": real_prices.ravel(),
    "Predicted": predicted_prices.ravel()
})


prediction_plot = stocks.hvplot()
prediction_plot
