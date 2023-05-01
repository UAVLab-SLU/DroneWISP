simplest openfoam project

create a cup that is filled with fluid, static environment

the entire environment is defined by the geometry vertices and faces in the file system/blockMeshDict

To run the simulation, run the following commands in the terminal:

```bash
blockMesh
icoFoam
```
this will create folder 0.1 -> 0.5 with the results of the simulation
where the number is the time step