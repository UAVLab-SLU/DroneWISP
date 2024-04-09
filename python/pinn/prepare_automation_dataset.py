from python.stl.mesh_utils import StlMeshUtils
import os
import numpy as np

output_dir = "../csv/train/surface_only"
stl_file = "../openFoamCase/constant/geometry/combined.stl"
stl_mesh_utils = StlMeshUtils(debug_mode=True)  # chicago dimensions: -2014 2073 -1710 1706 0 441
stl_mesh_utils.load_convert_mesh(stl_file)

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
    blocks = stl_mesh_utils.partition_mesh_block(block_size_x, block_size_y, x_min, x_max, y_min, y_max)
    print("block count: ", len(blocks))
    for i, block in enumerate(blocks):
        np.save(output_dir + os.sep + "binary_mask" + os.sep + "binary_mask_" + str(i) + ".npy", block)



prepare_mesh()



