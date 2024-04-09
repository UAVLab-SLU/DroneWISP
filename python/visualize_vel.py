import numpy as np
import matplotlib.pyplot as plt

vel_tensor = np.load("csv/train/100/velocity/velocity_0.npy").reshape((50, 50, 25, 3))
print(vel_tensor.shape)



def plot_velocity_array():
    """
    plot the velocity array, only 1s are plotted
    :return:
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title('Ground Truth Wind Velocity')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    draw_step = 5

    for x in range(-50, 50, draw_step):
        for y in range(-50, 50, draw_step):
            for z in range(0, 25, draw_step):
                u = vel_tensor[x, y, z][0]
                v = vel_tensor[x, y, z][1]
                w = vel_tensor[x, y, z][2]
                # color based on magnitude
                wind_velocity = np.linalg.norm(vel_tensor[x, y, z])
                rgb_red = int(255 * (wind_velocity / 50))
                if rgb_red > 255:
                    rgb_red = 255
                ax.quiver(x, y, z, u, v, w, length=0.5, color=(rgb_red / 255, 0, 0))

    ax.set_xlim(-50, 50)
    ax.set_ylim(-50, 50)
    ax.set_zlim(0, 25)
    # view angle
    ax.view_init(45, 45)
    plt.show()

plot_velocity_array()
