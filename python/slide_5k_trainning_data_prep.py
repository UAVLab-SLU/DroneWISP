# Prepare 5k training data for PINN by sliding the boundary vertices in openfoam blockMeshDict file

import os
import numpy as np
from python.pyfoam_reader import OpenFoamController
import time

case_root = "openFoamCase"
foam = OpenFoamController(case_root)

# boundary vertices range, should not exceed the box formed by min_point and max_point
min_point = (-100, -100, 0)
max_point = (100, 100, 10)
offset = [0, 0, 0]
step_size = 25
x_size, y_size, z_size = 25, 25, 10

# how many times to slide the boundary vertices
offset_x_bound, offset_y_bound, offset_z_bound = 25, 25, 10
offset_x_step, offset_y_step, offset_z_step = 1, 1, 1

if offset_x_bound > x_size or offset_y_bound > y_size or offset_z_bound > z_size:
    raise ValueError("offset bound should not exceed the box sliding range, otherwise same data will be generated")

offset_x, offset_y, offset_z = 0, 0, 0  # comment out when using fine offset loops

count = 0
# sliding step, slide order (x, y) z axis don't matter
for offset_x in range(0, offset_x_bound, offset_x_step):
    for offset_y in range(0, offset_y_bound, offset_y_step):
        for offset_z in range(0, offset_z_bound, offset_z_step):
            print("offset: ", offset_x, offset_y, offset_z)
            for y in range(min_point[0], max_point[0], step_size):
                for x in range(min_point[1], max_point[1], step_size):
                    lower_bound = (x + offset_x, y + offset_y, min_point[2] + offset_z)
                    v_1 = (lower_bound[0], lower_bound[1], lower_bound[2])
                    v_2 = (lower_bound[0] + x_size, lower_bound[1], lower_bound[2])
                    v_3 = (lower_bound[0] + x_size, lower_bound[1] + y_size, lower_bound[2])
                    v_4 = (lower_bound[0], lower_bound[1] + y_size, lower_bound[2])
                    v_5 = (lower_bound[0], lower_bound[1], lower_bound[2] + z_size)
                    v_6 = (lower_bound[0] + x_size, lower_bound[1], lower_bound[2] + z_size)
                    v_7 = (lower_bound[0] + x_size, lower_bound[1] + y_size, lower_bound[2] + z_size)
                    v_8 = (lower_bound[0], lower_bound[1] + y_size, lower_bound[2] + z_size)
                    vertices = [v_1, v_2, v_3, v_4, v_5, v_6, v_7, v_8]
                    vertices_string = foam.vertices_to_string(vertices)

                    t_start = time.time()

                    foam.clean()

                    foam.update_vertices(vertices_string)
                    foam.update_dimension(x_size, y_size, z_size)
                    inside_point = foam.calculate_shm_inside_point(vertices)
                    print("inside_point: ", inside_point)
                    foam.update_shm_inside_point(inside_point)

                    # check if this specific box is already run
                    data_dir = os.path.join("../5k_training_dataset", str(v_1[0]) + "_" + str(v_7[0]),
                                            str(v_1[1]) + "_" + str(v_7[1]), str(v_1[2]) + "_" + str(v_7[2]))
                    if os.path.exists(data_dir):
                        print("Data already exists, Vertices: ", vertices, "inside_point: ", inside_point)
                        continue

                    foam.run()

                    if not foam.check_run_valid():
                        print("Error: invalid run, Vertices: ", vertices, "inside_point: ", inside_point)
                        foam.clean()
                        continue
                    else:
                        foam.pinn_save_all_result_and_preprocess(range_x=x_size, range_y=y_size, range_z=z_size,
                                                                 x_min=v_1[0], y_min=v_1[1], z_min=v_1[2],
                                                                 x_max=v_7[0], y_max=v_7[1], z_max=v_7[2])
                        print("time elapsed for 1 simulation: ", time.time() - t_start, "seconds")

print("Total partitions using fine offset: ", count)
