import pandas as pd
import numpy as np
from scipy.spatial import KDTree
import time
import matplotlib.pyplot as plt


class CoordinateLookup:
    def __init__(self, df):
        self.df = df
        self.tree = KDTree(df[['x', 'y', 'z']].values)

    def get_value(self, point):
        distance, index = self.tree.query(point)
        return self.df.iloc[index]['value']


# Function to generate a DataFrame of given size
def generate_dataframe(size):
    data = {
        'x': np.random.rand(size) * 100,
        'y': np.random.rand(size) * 100,
        'z': np.random.rand(size) * 100,
        'value': np.random.randint(0, 100, size)
    }
    return pd.DataFrame(data)


# Sizes to test
sizes = [100, 1000, 10000, 100000, 1000000, 10000000]

# Storage for results
build_times = []
query_times = []

# Point to query
test_point = [50, 50, 50]

for size in sizes:
    # Generate DataFrame
    df = generate_dataframe(size)

    # Measure KDTree build time
    start_time = time.time()
    lookup = CoordinateLookup(df)
    build_time = time.time() - start_time
    build_times.append(build_time)

    # Measure query time
    start_time = time.time()
    lookup.get_value(test_point)
    query_time = time.time() - start_time
    query_times.append(query_time)

    print(f"Size: {size}, Build Time: {build_time:.6f}s, Query Time: {query_time:.6f}s")

# Plotting results
plt.figure(figsize=(12, 6))

# Plot build times
plt.subplot(1, 2, 1)
plt.plot(sizes, build_times, marker='o')
plt.xscale('log')
plt.yscale('log')
plt.xlabel('DataFrame Size')
plt.ylabel('Build Time (seconds)')
plt.title('KDTree Build Time vs DataFrame Size')
plt.grid(True)

# Plot query times
plt.subplot(1, 2, 2)
plt.plot(sizes, query_times, marker='o')
plt.xscale('log')
plt.yscale('log')
plt.xlabel('DataFrame Size')
plt.ylabel('Query Time (seconds)')
plt.title('KDTree Query Time vs DataFrame Size')
plt.grid(True)

plt.tight_layout()
plt.show()
