# Tall building environment turbulence simulation

## Description
This is a simulation of the turbulent flow around multiple tall buildings.

## change wind speed
change the wind speed in the file of 0/U

modify the value of U in the file of 0/U
```cpp
inlet
    {
        type            turbulentInlet;
        referenceField  uniform (10 0 0);
        fluctuationScale (0.02 0.01 0.01);
        value           uniform (10 0 0);
    }
```
referenceField is the mean wind speed, represented by white color in paraview
value is the wind speed, change it to change the wind speed
fluctuationScale is the fluctuation of the wind speed, higher value means more fluctuation


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
paraFoam
```
this command will open the paraview, and automatically load the case
