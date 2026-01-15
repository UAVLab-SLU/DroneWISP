import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Path to your CSV file
csv_path = "height_map_chicago_park.csv"

# Load the data
df = pd.read_csv(csv_path)

# Plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(df["x"], df["y"], df["z"], s=10)

# Axis labels
ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.set_title("3D Scatter Plot of XYZ Data")

plt.show()
