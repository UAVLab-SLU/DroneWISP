import os.path
import time

import matplotlib.pyplot as plt
import numpy as np
import torch

from python.pinn.model.dnn_gen import DnnGenNet

if __name__ == "__main__":

    sample_size = 2
    draw_step = 5
    input_file = os.path.join('..', 'csv', 'train', '100', 'binary_mask', 'binary_mask_6.npy')
    ground_truth_file = os.path.join('..', 'csv', 'train', '100', 'velocity', 'velocity_6.npy')

    net = DnnGenNet(n_channels=1, n_classes=3, bilinear=False)
    print('Loading model...')
    net.load_state_dict(torch.load('dnn.pth'))

    input_test_mesh = np.load(input_file)
    print("input shape:", input_test_mesh.shape)  # shape: (50, 50, 25)
    ground_truth = np.load(ground_truth_file)
    ground_truth = ground_truth.reshape((50, 50, 25, 3))
    print("ground truth shape:", ground_truth.shape)  # shape: (50, 50, 25, 3)

    # ground truth
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title('Ground Truth Wind Velocity')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    # 2 steps
    for x in range(-50, 50, draw_step):
        for y in range(-50, 50, draw_step):
            for z in range(0, 25, draw_step):
                u = ground_truth[x, y, z][0]
                v = ground_truth[x, y, z][1]
                w = ground_truth[x, y, z][2]
                # color based on magnitude
                wind_velocity = np.linalg.norm(ground_truth[x, y, z])
                rgb_red = int(255 * (wind_velocity / 50))
                if rgb_red > 255:
                    rgb_red = 255
                ax.quiver(x, y, z, u, v, w, length=0.5, color=(rgb_red / 255, 0, 0))

    ax.set_xlim(-50, 50)
    ax.set_ylim(-50, 50)
    ax.set_zlim(0, 25)
    plt.show()

    # predict
    input_test_mesh_tensor = torch.from_numpy(input_test_mesh).float().unsqueeze(0).unsqueeze(0)
    start_time = time.time()
    output = net(input_test_mesh_tensor)
    print("inference time:", time.time() - start_time, "seconds")
    output = output.detach().numpy()
    output = output.reshape((50, 50, 25, 3))
    print("output shape:", output.shape)  # shape: (50, 50, 25, 3)
    # print(output)
    # print(ground_truth)
    print("MSE:", np.mean((output - ground_truth) ** 2))
    print("MAE:", np.mean(np.abs(output - ground_truth)))
    print("RMSE:", np.sqrt(np.mean((output - ground_truth) ** 2)))
    print("magnitude MSE:", np.mean((np.linalg.norm(output, axis=3) - np.linalg.norm(ground_truth, axis=3)) ** 2))

    # plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title('Predicted Wind Velocity')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    # 2 steps
    for x in range(-50, 50, draw_step):
        for y in range(-50, 50, draw_step):
            for z in range(0, 25, draw_step):
                u = output[x, y, z][0]
                v = output[x, y, z][1]
                w = output[x, y, z][2]
                wind_velocity = np.linalg.norm(output[x, y, z])
                rgb_red = int(255 * (wind_velocity / 50))
                if rgb_red > 255:
                    rgb_red = 255
                ax.quiver(x, y, z, u, v, w, length=0.5, color=(rgb_red / 255, 0, 0))
    ax.set_xlim(-50, 50)
    ax.set_ylim(-50, 50)
    ax.set_zlim(0, 25)
    plt.show()

    # grab a random sample of 10 and compare
    for i in range(sample_size):
        x = np.random.randint(-50, 50)
        y = np.random.randint(-50, 50)
        z = np.random.randint(0, 25)
        print("predicted wind velocity at (", x, ",", y, ",", z, "):", output[x, y, z],
              "wind magnitude:", np.linalg.norm(output[x, y, z]))
        print("ground truth wind velocity at (", x, ",", y, ",", z, "):", ground_truth[x, y, z],
              "wind magnitude:", np.linalg.norm(ground_truth[x, y, z]))
        print("magnitude difference:", np.linalg.norm(output[x, y, z]) - np.linalg.norm(ground_truth[x, y, z]))
        print("difference:", output[x, y, z] - ground_truth[x, y, z])
