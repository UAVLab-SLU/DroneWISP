# Tall building environment wind shear simulation

## Description
This is a simulation of the wind shear flow around multiple tall buildings, by creating two wind sources,
one toward +x, one toward -y

## change wind speed
change the wind speed in the file of 0/U
```cpp
inlet
    {
        type            turbulentInlet;
        referenceField  uniform (10 0 0);
        fluctuationScale (0.5 0.5 0.5);
        value           uniform (10 0 0);
    }

outlet
    {
        type            inletOutlet;
        inletValue      uniform (0 0 0);
        value           $internalField;
    }
    
   
back
    {
        type            turbulentInlet;
        referenceField  uniform (0 -10 0);
        fluctuationScale (0.5 0.5 0.5);
        value           uniform (0 -10 0);
    }


front
    {
       type            fixedValue;
       value           $internalField;
    }
```
To create two wind sources, one toward +x, one toward -y
use above initial wind speed condition in U file,

For -x, +y, change the inlet, outlet, front, back parameter reversely.

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
