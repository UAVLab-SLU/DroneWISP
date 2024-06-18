import pandas as pd
import numpy as np
from scipy.spatial import KDTree
import time
import matplotlib.pyplot as plt
import psutil


class CoordinateLookup:
    def __init__(self, df):
        self.df = df
        self.tree = KDTree(df[['x', 'y', 'z']].values)

    def get_value(self, point):
        distance, index = self.tree.query(point)
        return [self.df.iloc[index]['u'], self.df.iloc[index]['v'], self.df.iloc[index]['w']]


# Function to generate a DataFrame of given size
def generate_dataframe(size):
    data = {
        'x': np.random.rand(size) * 100,
        'y': np.random.rand(size) * 100,
        'z': np.random.rand(size) * 100,
        'u': np.random.rand(size) * 100,
        'v': np.random.rand(size) * 100,
        'w': np.random.rand(size) * 100,
    }
    return pd.DataFrame(data)


# Sizes to test
sizes = [100, 1000, 10000, 100000, 200000, 500000, 1000000]

# Storage for results
build_times = []
query_times = []

# Point to query
test_point = [5.8415646, 10.98659859, 15.12345678]

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

#
# # Benchmark for KD-trees of size 250,000
# tree_size = 250000
# tree_counts = [10, 50, 100, 200, 500]
#
# # Storage for results
# memory_usages = []
#
# for num_trees in tree_counts:
#     trees = []
#     start_memory = psutil.virtual_memory().used
#
#     start_time = time.time()
#     for _ in range(num_trees):
#         df = generate_dataframe(tree_size)
#         trees.append(CoordinateLookup(df))
#     total_time = time.time() - start_time
#     end_memory = psutil.virtual_memory().used
#
#     memory_used = (end_memory - start_memory) / (1024 ** 2)  # Convert to MB
#     memory_usages.append(memory_used)
#
#     print(f"Loaded {num_trees} KD-trees of size {tree_size} in {total_time:.6f} seconds")
#     print(f"Total memory used: {memory_used:.2f} MB")


# Plotting results
plt.figure(figsize=(18, 6))

# Plot build times
plt.subplot(1, 3, 1)
plt.plot(sizes, build_times, marker='o')
plt.xscale('log')
plt.yscale('log')
plt.xlabel('DataFrame Size')
plt.ylabel('Build Time (seconds)')
plt.title('KDTree Build Time vs DataFrame Size')
plt.grid(True)

# Plot query times
plt.subplot(1, 3, 2)
plt.plot(sizes, query_times, marker='o')
plt.xscale('log')
plt.yscale('log')
plt.xlabel('DataFrame Size')
plt.ylabel('Query Time (seconds)')
plt.title('KDTree Query Time vs DataFrame Size')
plt.grid(True)

# # Plot memory usage
# plt.subplot(1, 3, 3)
# plt.plot(tree_counts, memory_usages, marker='o')
# plt.xlabel('Number of KD-Trees')
# plt.ylabel('Memory Usage (MB)')
# plt.title('Memory Usage vs Number of KD-Trees')
# plt.grid(True)

plt.tight_layout()
plt.show()
