# Importing necessary libraries
from anfis.anfis import predict
import numpy as np
import pickle
import matplotlib.pyplot as plt

with open('anfisModel.pkl', 'rb') as inp:
    anf = pickle.load(inp)

# Parameters for noise
noise_level = 0.1  # Adjust this to control the noise intensity

# Extend the time range to predict the next 2,000 points
t_future = np.linspace(1, 2, 1000)  # Time steps for the next 2,000 points
# x1_future = np.sin(0.02 * t_future)  # Sine wave
# x2_future = np.cos(0.02 * t_future)  # Cosine wave
x1_future = t_future
x2_future = np.cos(0.02 * t_future)  # Cosine wave
y = np.sin((0.02 * t_future + np.pi/4)*100) + 0.1*np.random.normal(0, noise_level, t_future.shape)

# Stack the future features (this would be the input for prediction)
X_future = np.column_stack((x1_future, x2_future))

# Use the trained ANFIS model to predict the output for these new points
Y_pred = predict(anf, X_future)

# Plot the predictions
plt.figure(figsize=(10, 5))
plt.plot(t_future, Y_pred, label='Predicted Output', color='blue')
plt.plot(t_future, y, label='Actual Output', color='red')
plt.xlabel('Time')
plt.ylabel('Predicted Value')
plt.title('Predictions for the Next 2000 Points')
plt.legend()
plt.grid(True)
plt.show()
