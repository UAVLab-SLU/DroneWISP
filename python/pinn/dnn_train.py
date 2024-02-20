import os.path

import torch
import torch.nn as nn
import numpy as np
from python.pinn.model.dnn_gen import DnnGenNet

def linear_interpolate(outputs, idx):
    """
    Interpolate the wind speed at the given indices using trilinear interpolation
    :param outputs:
    :param idx:
    :return:
    """
    # Get indices for the neighboring points
    x0 = torch.clamp(idx[..., 0], 0, outputs.size(2) - 1)
    x1 = torch.clamp(idx[..., 0] + 1, 0, outputs.size(2) - 1)
    y0 = torch.clamp(idx[..., 1], 0, outputs.size(3) - 1)
    y1 = torch.clamp(idx[..., 1] + 1, 0, outputs.size(3) - 1)
    z0 = torch.clamp(idx[..., 2], 0, outputs.size(4) - 1)
    z1 = torch.clamp(idx[..., 2] + 1, 0, outputs.size(4) - 1)

    # Calculate weights for interpolation
    wx1 = (x1 - idx[..., 0]) / (x1 - x0 + 1e-6)
    wx0 = 1 - wx1
    wy1 = (y1 - idx[..., 1]) / (y1 - y0 + 1e-6)
    wy0 = 1 - wy1
    wz1 = (z1 - idx[..., 2]) / (z1 - z0 + 1e-6)
    wz0 = 1 - wz1

    # Interpolate along each axis
    interp_values = (
        wx0 * wy0 * wz0 * outputs[:, :, x0, y0, z0] +
        wx1 * wy0 * wz0 * outputs[:, :, x1, y0, z0] +
        wx0 * wy1 * wz0 * outputs[:, :, x0, y1, z0] +
        wx1 * wy1 * wz0 * outputs[:, :, x1, y1, z0] +
        wx0 * wy0 * wz1 * outputs[:, :, x0, y0, z1] +
        wx1 * wy0 * wz1 * outputs[:, :, x1, y0, z1] +
        wx0 * wy1 * wz1 * outputs[:, :, x0, y1, z1] +
        wx1 * wy1 * wz1 * outputs[:, :, x1, y1, z1]
    )

    return interp_values

def physics_loss_linear_interpolate(outputs):
    """
    Calculate the physics loss using trilinear interpolation
    :param outputs: (batch, channel, x, y, z)
    :return: loss
    """
    # Create a grid of indices
    idx = torch.stack(torch.meshgrid(
        torch.arange(outputs.size(2)),
        torch.arange(outputs.size(3)),
        torch.arange(outputs.size(4))
    ), dim=-1).to(outputs.device)

    # Calculate interpolated wind speed at each point
    interp_values = linear_interpolate(outputs, idx)

    # Calculate the discrepancy between the predicted wind speed and the interpolated value
    discrepancy = torch.abs(outputs - interp_values)

    # Sum up the discrepancy and normalize by the number of samples
    loss = torch.sum(discrepancy) / discrepancy.numel()

    return loss


if __name__ == "__main__":
    # use gpu if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Using device:', device)

    # Load data
    load_model = True
    train_model = True
    save_model = True
    epoch_per_run = 1000
    training_file_dir = os.path.join('..', 'csv', 'train', '100')

    mesh_files = os.listdir(os.path.join(training_file_dir, 'binary_mask'))
    mesh_files = [os.path.join(training_file_dir, 'binary_mask', file) for file in mesh_files]
    mesh_files.sort()

    vl_files = os.listdir(os.path.join(training_file_dir, 'velocity'))
    vl_files = [os.path.join(training_file_dir, 'velocity', file) for file in vl_files]
    vl_files.sort()

    for mesh_file, vl_file in zip(mesh_files, vl_files):
        mesh = np.load(mesh_file)
        wind_velocity = np.load(vl_file)
        # col 4 5 6 are the wind velocity
        # Convert data to tensors [batch, channel, x, y, z]
        mesh_tensor = torch.from_numpy(mesh).float().unsqueeze(0).unsqueeze(0)
        wind_velocity_tensor = torch.from_numpy(wind_velocity).float()
        ground_truth_tensor = torch.tensor(wind_velocity_tensor, requires_grad=False)

        print('mesh_tensor:', mesh_tensor.shape)
        print('wind_velocity_tensor:', wind_velocity_tensor.shape)

        # Initialize the DNN
        net = DnnGenNet(n_channels=1, n_classes=3, bilinear=False)

        # Define a loss function and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(net.parameters(), lr=0.001)

        if load_model:
            print('Loading model...')
            net.load_state_dict(torch.load('dnn.pth'))
        if train_model:
            # Train the network
            for epoch in range(epoch_per_run):  # Loop over the dataset multiple times
                print('Epoch:', epoch + 1)
                running_loss = 0.0
                # Zero the parameter gradients
                optimizer.zero_grad()

                # Forward + backward + optimize
                outputs = net(mesh_tensor)  # Pass the mesh tensor directly
                print('outputs:', outputs.shape)
                print('wind_velocity_tensor:', wind_velocity_tensor.shape)
                # outputs: torch.Size([1, 3, 50, 50, 25])
                # wind_velocity_tensor: torch.Size([62500, 3])
                # reshape wind_velocity_tensor to match the outputs

                # calculate physics loss
                physics_loss = physics_loss_linear_interpolate(outputs)

                loss = criterion(outputs, wind_velocity_tensor.view(1, 3, 50, 50, 25)) + physics_loss
                loss.backward()
                optimizer.step()

                # Print statistics
                running_loss += loss.item()

                if epoch % 2 == 1:
                    print('[%d] loss: %.3f' % (epoch + 1, running_loss / 2000))
                    running_loss = 0.0

            print('Finished Training')
        if save_model:
            print('Saving model...')
            torch.save(net.state_dict(), 'dnn.pth')
