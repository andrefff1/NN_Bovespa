# Importing necessary libraries

import pandas as pd
from anfis import membershipfunction
from anfis.anfis import ANFIS
import numpy as np
from scipy.spatial.distance import pdist, squareform
from sklearn.utils import resample, shuffle
import pickle
from sklearn.preprocessing import StandardScaler

# Extract data
data = pd.read_csv('../../ETL/Load/stockData.csv', header=(0), sep=';')

# Replace inf values by very large number
data.replace(np.inf, 1e20, inplace=True)

# Separate train data
# Train: first 8 years
data['DATE'] = pd.to_datetime(data['DATE'])
data_train = data[data['DATE'].dt.year <= 2021]

# Change data to numpy
data_train = data_train.to_numpy()

# Get number of rows and columns
ncol = data.shape[1]

# Get arrays for features and class
#y_train = data_train[:, -1]
#X_train = data_train[:, 2:ncol-1]
y_train = data_train[:, -1]
X_train = data_train[:, 2:4]
#X_train = X_train.reshape(-1, 1)

# Scale the data
scaler = StandardScaler().fit(X_train)
X_train = scaler.transform(X_train)


# Upsample 1 Class
# Convert X_train and y_train to DataFrame and Series, respectively
X_train = pd.DataFrame(X_train)
y_train = pd.Series(y_train)

# Split the dataset by class
X_train_majority = X_train[y_train == 0]
X_train_minority = X_train[y_train == 1]

y_train_majority = y_train[y_train == 0]
y_train_minority = y_train[y_train == 1]

# Resample minority class to match the majority class size
X_train_minority_upsampled = resample(X_train_minority,
                                      replace=True,
                                      n_samples=len(X_train_majority),
                                      random_state=42)

y_train_minority_upsampled = resample(y_train_minority,
                                      replace=True,
                                      n_samples=len(y_train_majority),
                                      random_state=42)

# Combine majority class and upsampled minority class
X_train_balanced = pd.concat([X_train_majority, X_train_minority_upsampled])
y_train_balanced = pd.concat([y_train_majority, y_train_minority_upsampled])

# Shuffle the data
X_train_balanced, y_train_balanced = shuffle(X_train_balanced, y_train_balanced, random_state=42)

# Change data to numpy
X_train_balanced = X_train_balanced.to_numpy()
y_train_balanced = y_train_balanced.to_numpy()

# Convert y to integer
y_train_balanced = y_train_balanced.astype(int)

# Set the number of rules
number_of_rules = 2


# Subtractive clustering with radius = 0.2
def subtractive_clustering(X, number_of_rules, radius=0.2):
    # Compute pairwise distances between points
    d = pdist(X, 'euclidean')
    d_squareform = squareform(d)
    # Calculate potential for each point
    potential = np.sum(np.exp(-d_squareform**2 / (radius/2)**2), axis=1)
    # Sort by potential and select two highest points (for two rules)
    idx = np.argsort(potential)[::-1][:number_of_rules]
    print(potential)
    print(np.argsort(potential))
    return X[idx]


# Apply clustering to get rule centers
rule_centers = subtractive_clustering(X_train_balanced, number_of_rules, radius=0.2)
print("Rule Centers:", rule_centers)

# Create Gaussian membership functions centered at the rule centers
mfs = []  # Initialize the mf list
for i in range(X_train_balanced.shape[1]):
    mf = []
    for j in range(number_of_rules):
        mf.append(['gaussmf', {'mean': rule_centers[j][i], 'sigma': 100.0}])
    mfs.append(mf)

# Updating the model with Membership Functions
mfc = membershipfunction.MemFuncs(mfs)
# Creating the ANFIS Model Object
anf = ANFIS(X_train_balanced,  y_train_balanced,  mfc)
# Fitting the ANFIS Model
print('Training model...')
anf.trainHybridJangOffLine(epochs=20, tolerance=1e-8)
# Printing Output
print(round(anf.consequents[-1][0], 6))
print(round(anf.consequents[-2][0], 6))
print(round(anf.fittedValues[9][0], 6))
# Plotting Model Performance
anf.plotErrors()
anf.plotResults()

with open('anfisModel.pkl', 'wb') as outp:
    pickle.dump(anf, outp, pickle.HIGHEST_PROTOCOL)
