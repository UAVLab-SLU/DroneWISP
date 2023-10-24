# Chicago digital twin environment constant wind simulation

## Description
This is a simulation of the constant wind speed around Chicago digital twin environment.

## change wind speed
change the wind speed in the file of 0/include/
```cpp
flowVelocity         (10 0 0);
```
above condition represents the wind speed of 10m/s towards +x direction

## How to use
### run:
```bash
bash ./Allrun
```
to run the simulation

### clean:
```bash
bash ./Allclean
```
to clean the simulation

## Result
to see the result, you can use paraview in the directory of blockEnv
```bash
paraFoam &
```

