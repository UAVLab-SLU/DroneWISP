# Chicago digital twin environment turbulent wind simulation

## Description
This is a simulation of turbulent wind around Chicago digital twin environment,
created by fluctuating the wind speed by given turbulence percentage.


## change wind speed
change the mean wind speed in the file of 0/U
```cpp
inlet
    {
        type            turbulentInlet;
        referenceField  uniform (10 0 0);
        fluctuationScale (0.5 0.5 0.5);
        value           uniform (10 0 0);
    }
```
where type is the inlet type, 
referenceField is the mean wind speed, 
fluctuationScale is the turbulence percentage, 
value is the original wind speed.

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

