# RealisticWind

This project uses OpenFoam to simulate realist wind conditions for a given geometry. 

## Getting Started
### install openfoam on windows linux subsystem
install linux subsystem
```commandline
wsl --install
```
Distributor ID: Ubuntu
Description:    Ubuntu 22.04.1 LTS
Release:        22.04
Codename:       jammy

```bash
sudo sh -c "wget -O - [http://dl.openfoam.org/gpg.key](http://dl.openfoam.org/gpg.key) | apt-key add -"

sudo add-apt-repository [http://dl.openfoam.org/ubuntu](http://dl.openfoam.org/ubuntu)

sudo apt-get update

sudo apt-get install openfoam10

sudo apt-get install --only-upgrade openfoam10
```



## Directory Structure
all executable are in the run directory
```bash
cd run
```
detailed description of each example is in the readme.md file in each directory


