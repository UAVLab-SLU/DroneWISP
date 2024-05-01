from mesh_utils import StlMeshUtils

mesh_utils = StlMeshUtils()
# vertices = [
#     (0, 0, 0),
#     (100, 0, 0),
#     (100, 100, 0),
#     (0, 100, 0),
#     (0, 0, 25),
#     (100, 0, 25),
#     (100, 100, 25),
#     (0, 100, 25),
# ]

vertices = [
    (-50, -50, 0),
    (50, -50, 0),
    (50, 50, 0),
    (-50, 50, 0),
    (-50, -50, 25),
    (50, -50, 25),
    (50, 50, 25),
    (-50, 50, 25),
]

input_stl = "../openFoamCase/constant/geometry/ChicagoCentered.stl"
out_stl = "../openFoamCase/constant/geometry/combined.stl"

mesh_utils.clip_and_save_mesh(vertices, input_stl, out_stl)
