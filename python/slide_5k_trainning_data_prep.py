# Prepare 5k training data for PINN by sliding the boundary vertices in openfoam blockMeshDict file

import os
import numpy as np
from python.pyfoam_reader import OpenFoamController

case_root = "openFoamCase"
foam = OpenFoamController(case_root)

def check_box_valid(vertices):
    """
    check if the box formed by the vertices is valid
    :param vertices: 8 vertices of the box, [v_1, v_2, v_3, v_4, v_5, v_6, v_7, v_8], v_i = (x, y, z)
    :return: bool
    """


# boundary vertices range, should not exceed the box formed by min_point and max_point
min_point = (-1000, -1000, 0)
max_point = (1000, 1000, 25)
offset = [0, 0, 0]
step_size = 100
x_size, y_size, z_size = 50, 50, 25

count = 0
# sliding step, slide order (x, y) z axis don't matter
for offset_x in range(0, x_size,1):
    for offset_y in range(0, y_size, 1):
        for offset_z in range(0, z_size, 1):
            print("offset: ", offset_x, offset_y, offset_z)
            for x in range(min_point[0], max_point[0], step_size):
                for y in range(min_point[1], max_point[1], step_size):
                    min_bound = (x + offset_x, y + offset_y, min_point[2]+offset_z)
                    max_bound = (x + offset_x, y + offset_y, max_point[2]+offset_z)
                    v_1 = (min_bound[0], min_bound[1], min_bound[2])
                    v_2 = (max_bound[0]+x_size, min_bound[1], min_bound[2])
                    v_3 = (max_bound[0]+x_size, max_bound[1]+y_size, min_bound[2])
                    v_4 = (min_bound[0], max_bound[1]+y_size, min_bound[2])
                    v_5 = (min_bound[0], min_bound[1], max_bound[2]+z_size)
                    v_6 = (max_bound[0]+x_size, min_bound[1], max_bound[2]+z_size)
                    v_7 = (max_bound[0]+x_size, max_bound[1]+y_size, max_bound[2]+z_size)
                    v_8 = (min_bound[0], max_bound[1]+y_size, max_bound[2]+z_size)
                    vertices = [v_1, v_2, v_3, v_4, v_5, v_6, v_7, v_8]
                    # TODO: finish inside point, boundary and range prep
                    print(vertices)
                    count += 1

print("Total partitions using fine offset: ", count)


