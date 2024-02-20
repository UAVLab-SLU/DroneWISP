import os.path

import torch
import torch.nn as nn
import numpy as np
from python.pinn.model.dnn_gen import DnnGenNet

if __name__ == "__main__":
    # use gpu if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Using device:', device)

    # Load data
    load_model = True
    train_model = True
    save_model = True
    epoch_per_run = 10
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
                loss = criterion(outputs, wind_velocity_tensor.view(1, 3, 50, 50, 25))
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
