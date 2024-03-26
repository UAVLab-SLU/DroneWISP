from python.stl.mesh_utils import StlMeshUtils
from python.auto_preprocess_all_for_train import preprocess_all
import os
import numpy as np
import matplotlib.pyplot as plt

output_dir = "../csv/train/100"
openfoam_case_root = "../openFoamCase"
init_filename = "10ms_0.csv"
use_strong_preprocessing = True
stl_file = "../openFoamCase/constant/geometry/combined.stl"
vl_file = "../openFoamCase/10ms_2.csv"
stl_mesh_utils = StlMeshUtils(debug_mode=True)  # chicago dimensions: -2014 2073 -1710 1706 0 441
# stl_mesh_utils.pv_load_convert_mesh(stl_file)  # pv version
stl_mesh_utils.load_convert_mesh(stl_file)  # o3d version

block_size_x = 50
block_size_y = 50
block_size_z = 25
x_min = -100
x_max = 100
y_min = -100
y_max = 100
z_min = 0
z_max = 25


def prepare_mesh():
    blocks = stl_mesh_utils.pv_partition_binary_mesh_block(block_size_x, block_size_y, block_size_z,
                                                           x_min, x_max,
                                                           y_min, y_max, block_size_z)


    print("block count: ", len(blocks))
    print("block shape: ", blocks[0].shape)
    for i, block in enumerate(blocks):
        np.save(output_dir + os.sep + "binary_mask" + os.sep + "binary_mask_" + str(i) + ".npy", block)

def prepare_mesh_o3d():
    # o3d
    blocks = stl_mesh_utils.partition_mesh_block(block_size_x, block_size_y,
                                                        x_min, x_max,
                                                        y_min, y_max)

    for i in range(len(blocks)):
        blocks[i] = stl_mesh_utils.to_binary_mask(blocks[i])


    print("block count: ", len(blocks))
    print("block shape: ", blocks[0].shape)
    for i, block in enumerate(blocks):
        np.save(output_dir + os.sep + "binary_mask" + os.sep + "binary_mask_" + str(i) + ".npy", block)


def prepare_velocity():
    stl_mesh_utils.load_velocity(vl_file)
    vel_blocks = stl_mesh_utils.partition_velocity_block(block_size_x, block_size_y, x_min, x_max, y_min, y_max)
    print("vel block count: ", len(vel_blocks))
    for i, block in enumerate(vel_blocks):
        np.save(output_dir + os.sep + "velocity" + os.sep + "velocity_" + str(i) + ".npy", block)
    # plot the first block


# prepare_mesh()
prepare_mesh_o3d()
prepare_velocity()
