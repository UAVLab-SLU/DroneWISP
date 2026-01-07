# system directory structure

## blockMeshDict 
Define the mesh structure of the boundaries and the number of points or accuracy of the block mesh.

## controlDict 
Define the total simulation time, time step, write interval, etc.

## snappyHexMeshDict 
Define the mesh structure of the internal domain and the number of points or accuracy of the snappyHexMesh. 
also allows to define the refinement level of the mesh in the vicinity of the boundaries, aka LOD (level of detail).

### Other files are not important for now, since they were already tuned for air flows simulations.