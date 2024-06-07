
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plot_data(csv_file, z_level):
    """
    Plot u v velocity data from the csv file at x y coordinates at a certain z level
    csv header: x,y,z,u,v,w,p,k,nut,omega,bm
    use color to represent the velocity magnitude.
    :param csv_file: Path to the CSV file
    :param z_level: The specific z-level to filter the data
    :return: None
    """

    # Load the data
    df = pd.read_csv(csv_file)

    # Filter the data to include only rows where z is equal to z_level
    filtered_df = df[df['z'] == z_level]

    # Compute the velocity magnitude
    filtered_df['velocity_magnitude'] = np.sqrt(filtered_df['u'] ** 2 + filtered_df['v'] ** 2)

    # Create the plot
    plt.figure(figsize=(10, 8))

    # Scatter plot with color representing velocity magnitude
    scatter = plt.scatter(filtered_df['x'], filtered_df['y'], c=filtered_df['velocity_magnitude'], cmap='viridis', s=50)
    plt.colorbar(scatter, label='Velocity Magnitude')

    # Labels and title
    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title(f'Velocity Field at Z = {z_level}')

    # Show the plot
    plt.show()

plot_data('pinn/cesium5kTrain/1c2b0044df5fc2d5e95c0060136268309726c7e2d0e8924a5e56b84530c6448a_-13_-17/-25_25_-25_25_0_10/result_preprocessed_50.csv'
          , 2)