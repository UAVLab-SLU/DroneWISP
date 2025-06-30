import pandas as pd
import time

HDF5_PATH = "openFoamCase/wisp_50.h5"
KEY = "velocity"  # This should match the `to_hdf(..., key="velocity")` used in saving

# Load entire dataset into memory
print(f"Loading HDF5 file: {HDF5_PATH}")
start_time = time.time()
df = pd.read_hdf(HDF5_PATH, key=KEY)
print(f"Loaded {len(df)} rows in {time.time() - start_time:.3f} seconds")

# Test: Read one location
test_point = (0, 0, 10)
x, y, z = test_point
start = time.time()
match = df[(df["x"] == x) & (df["y"] == y) & (df["z"] == z)]
elapsed = time.time() - start
if not match.empty:
    u, v, w = match.iloc[0][["u", "v", "w"]].tolist()
    print(f"Velocity at {test_point}: ({u:.2f}, {v:.2f}, {w:.2f}) [queried in {elapsed:.6f}s]")
else:
    print(f"Point {test_point} not found [queried in {elapsed:.6f}s]")

# Test: Query square region (e.g., x in [-5,5], y in [-5,5], z fixed)
x_range = range(-5, 6)
y_range = range(-5, 6)
z_fixed = 0

region_points = [(x, y, z_fixed) for x in x_range for y in y_range]

start = time.time()
results = []
for x, y, z in region_points:
    match = df[(df["x"] == x) & (df["y"] == y) & (df["z"] == z)]
    if not match.empty:
        results.append(match.iloc[0][["u", "v", "w"]].tolist())
elapsed = time.time() - start

print(f"Queried {len(region_points)} points in {elapsed:.4f}s, found {len(results)} valid entries")
