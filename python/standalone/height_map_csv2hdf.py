import pandas as pd
import numpy as np
import h5py

# Paths
csv_path = "height_map_chicago_park.csv"
h5_path = csv_path.replace(".csv", ".h5")

# Read CSV into DataFrame
df = pd.read_csv(csv_path)

# Ensure the DataFrame has the required columns
required_cols = ["x", "y", "z"]
if not all(col in df.columns for col in required_cols):
    raise ValueError(f"CSV file must contain columns: {required_cols}")

# Define structured dtype
dtype = np.dtype([
    ("x", "i4"), ("y", "i4"), ("z", "i4")
])

# Convert to structured array
structured_array = np.array(
    [tuple(row) for row in df[["x", "y", "z"]].values],
    dtype=dtype
)

# Write to HDF5
with h5py.File(h5_path, "w") as f:
    f.create_dataset("positions", data=structured_array)
