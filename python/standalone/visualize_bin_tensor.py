import numpy as np
import matplotlib.pyplot as plt

binary_tensor = np.load("csv/train/100/binary_mask/binary_mask_2.npy")
print(binary_tensor.shape)
#(50, 50, 25)

def plot_binary_array(array):
    """
    plot the binary array, only 1s are plotted
    :return:
    """

    figure = plt.figure()
    axes = figure.add_subplot(projection='3d')
    # axes.voxels(self.binary_array, edgecolor='k')
    x = []
    y = []
    z = []
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            for k in range(array.shape[2]):
                if array[i][j][k]:
                    x.append(i)
                    y.append(j)
                    z.append(k)

    axes.scatter(x, y, z, marker='.', s=1)
    axes.view_init(45, 45)
    axes.set_xlabel('X')
    axes.set_ylabel('Y')
    axes.set_zlabel('Z')

    # save
    plt.savefig("binary_tensor.png")

    plt.show()

plot_binary_array(binary_tensor)
