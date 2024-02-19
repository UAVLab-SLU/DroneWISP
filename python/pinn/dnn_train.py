import os.path

import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from python.pinn.model.dnn_gen import DnnGenNet

if __name__ == "__main__":
    # Load data
    load_model = True
    train_model = True
    training_fild_dir = os.path.join('..', 'csv', 'train', '100')

    mesh_files = os.listdir(os.path.join(training_fild_dir, 'binary_mask'))
    mesh_files = [os.path.join(training_fild_dir, 'binary_mask', file) for file in mesh_files]
    mesh_files.sort()

    vl_files = os.listdir(os.path.join(training_fild_dir, 'velocity'))
    vl_files = [os.path.join(training_fild_dir, 'velocity', file) for file in vl_files]
    vl_files.sort()

    for mesh_file, vl_file in zip(mesh_files, vl_files):
        mesh = np.load(mesh_file)
        wind_velocity = np.load(vl_file)
        # quick shape check
        print(mesh.shape, wind_velocity.shape)
        # col 4 5 6 are the wind velocity
        # Convert data to tensors
        mesh_tensor = torch.from_numpy(mesh).float()
        wind_velocity_tensor = torch.from_numpy(wind_velocity).float()
        ground_truth_tensor = torch.tensor(wind_velocity_tensor, requires_grad=False)

        # Initialize the DNN
        net = DnnGenNet()

        # Define a loss function and optimizer
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(net.parameters(), lr=0.001)

        if load_model:
            print('Loading model...')
            net.load_state_dict(torch.load('dnn.pth'))
        if train_model:
            # Train the network
            for epoch in range(10):  # Loop over the dataset multiple times
                print('Epoch:', epoch + 1)
                running_loss = 0.0
                # Zero the parameter gradients
                optimizer.zero_grad()

                # Forward + backward + optimize
                outputs = net(mesh_tensor.unsqueeze(0))
                loss = criterion(outputs, wind_velocity_tensor.view(1, -1))
                loss.backward()
                optimizer.step()

                # Print statistics
                running_loss += loss.item()

                if epoch % 2 == 1:
                    print('[%d] loss: %.3f' % (epoch + 1, running_loss / 2000))
                    running_loss = 0.0

            print('Finished Training')
            print('Saving model...')
            torch.save(net.state_dict(), 'dnn.pth')

        # # Perform inference
        # net.eval()  # Set the model to evaluation mode
        # with torch.no_grad():  # Turn off gradients for prediction
        #     outputs = net(mesh_tensor.unsqueeze(0))
        #     predicted_wind_velocity = outputs.view(50, 50, 25, 3)
