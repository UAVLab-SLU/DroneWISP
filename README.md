# DroneWISP (Wind Simulation and Prediction)
DroneWISP, or WISP for short, is a project that aims to simulate wind conditions for a given geometry and predict the wind velocity field using a PINN model.

(DroneWISP was previously known as RWDS, or Real Wind Drone Sim (RWDS), but was renamed to better reflect the project's goals.)

DRV, or Drone Req Validator, is a project that aims to streamline the process of validating the requirements of a drone software system. available at [here](https://github.com/UAVLab-SLU/AirsimMonitors)

This project uses OpenFoam to simulate realist wind conditions for a given geometry. Also propose a PINN model to predict the wind velocity field in the given geometry.

## Requirements
- Linux or WSL (WSL preferred)
- OpenFoam 10
- ParaView (optional, for visualization)
  - WSL users: Windows ParaView is recommended (see setup below)

## Hardware suggestion
- 6+ cores CPU
- 8GB+ RAM
- 20GB+ available storage

## Port reservation
- DRV REST: port 5000
- WISP REST: port 5001
- WISP UDP inbound: port 3001
- UE UDP inbound port: 8008
- UE UDP outbound target port: 3001


## Getting Started
### install openfoam on WSL or Linux
install linux subsystem, ignore if you are using linux natively
```commandline
wsl --install
```
Distributor ID: Ubuntu
Description:    Ubuntu 22.04.1 LTS
Release:        22.04
Codename:       jammy

After installing WSL, open the terminal and
run setup.sh
```bash
sudo bash setup.sh
```

Verify the installation by running the following command
```bash
foamVersion
```
Should return
```text
OpenFOAM 10
```

If that didn't work, follow the following steps to install OpenFoam 10 on WSL manually
```bash
sudo sh -c "wget -O - http://dl.openfoam.org/gpg.key | apt-key add -"
sudo add-apt-repository http://dl.openfoam.org/ubuntu
sudo apt-get update
sudo apt-get install openfoam10
sudo apt-get install --only-upgrade openfoam10
```

next add the following line to the end of file `.bashrc`
```text
source /opt/openfoam10/etc/bashrc
```
or run the following command
```bash
echo "source /opt/openfoam10/etc/bashrc" >> ~/.bashrc
```

source the new bashrc file
```bash
source ~/.bashrc
```

### Python virtual environment
```bash
cd python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```


### install openfoam on windows natively
NOT SUPPORTED

### install openfoam on mac
Docker is recommended for Mac users.

### WISP backend on docker
build the docker image
```bash
cd python
docker build -t wisp_server .
```
run the docker image
(assume you are in `python` directory)
```bash
docker compose up
```

### Workflow Runner batch interface
Use `compose.workflow-runner.yaml` to run a one-shot CFD job that accepts an STL terrain, wind definitions, and a target CSV path.

Local example:
```bash
bash run_wr_job.sh \
  --stl /home/bohanzhang/DroneWISP/4drone_Test_site_V36_mono_smooth.stl \
  --output /home/bohanzhang/DroneWISP/out/wind.csv \
  --wind-file /home/bohanzhang/DroneWISP/sim_config_3_drone.json
```

The wrapper extracts `environment.wind` when you pass a full simulation config JSON. It also supports `--wind-json` if WR already renders the wind payload directly.

Compose contract:
- `WR_INPUT_STL_DIR`: host directory that contains the STL file
- `WR_INPUT_STL_FILE`: STL basename inside that directory
- `WR_OUTPUT_DIR`: host directory where the merged CSV should be written
- `WR_OUTPUT_FILE`: output CSV basename
- `WR_WIND_JSON`: JSON array or object describing the wind input. A full config JSON with `environment.wind` also works

Optional environment values:
- `WR_DIRECTION_CONVENTION`: `to` by default. Set `from` if wind directions describe the source direction instead of the flow direction
- `WR_CONTROL_JSON`: optional JSON object with `dt`, `end_time`, and `write_interval`
- `WR_BOUNDS_JSON`: optional JSON object with `x_min`, `x_max`, `y_min`, `y_max`, `z_min`, `z_max`. When supplied, the runner clips the STL to that box before solving
- `WR_MESH_PADDING_JSON`: optional auto-bounds padding JSON, defaults to `{"xy":1,"z_min":1,"z_max":1}`
- `WR_FILL_MISSING`: defaults to `false`. Set `true` to backfill missing integer grid cells in the exported CSV

Multi-source wind handling:
- wind vectors are averaged component-wise
- the merged run is treated as `Turbulent Wind` if any source is turbulent
- `fluctuation_percentage` is taken as the maximum source value when turbulence is enabled

Notes:
- the exported CSV contains only the final time step with columns `x,y,z,u,v,w`
- large terrain meshes should usually provide `WR_BOUNDS_JSON` or a pre-clipped STL, otherwise the OpenFOAM domain may become too large to solve efficiently

## Directory Structure
all OpenFOAM research scenarios are in the run directory
```bash
cd run
```

detailed description of each example is in the readme.md file in each directory

In general, run the following command to run the simulation
```bash
cd run
cd {example directory}
bash ./Allrun
```

### Python entry points

#### WISP
start WISP side flask server: `python3 cfd_server.py -h "0.0.0.0" -p 5001`


#### PINN
preprocess velocity csv: `auto_preprocess_all_for_sim.py`, `auto_preprocess_all_for_train.py`. for sim uses weak preprocessing, for train uses strong preprocessing.

prepare training data: `pinn/prepare_training_dataset.py` 

train the model: `pinn/dnn_train.py`

test the model: `pinn/dnn_test.py`






## How to use ParaView

### Setting up Windows ParaView for WSL (Recommended)

If you're using WSL and have ParaView installed on Windows, you can configure the system to use Windows ParaView instead of the WSL version. This avoids segfault issues with WSL ParaView and provides better performance.

Run the setup script from the main directory:
```bash
cd /path/to/DroneWISP
bash ./setup_paraview_windows.sh
```

This script will:
- Configure your shell to use Windows ParaView (`G:\ParaView 5.13.2\bin\paraview.exe`) by default
- Automatically convert WSL paths to Windows network paths
- Fall back to WSL paraFoam if Windows ParaView is not found

After running the script, either:
- Open a new terminal window, or
- Run `source ~/.bashrc` in your current terminal

**Note:** If your ParaView installation is in a different location, edit `setup_paraview_windows.sh` and update the `PARAVIEW_EXE` path.

### Visualizing the results
To visualize the results of the simulation, you can use ParaView.
```bash
cd run
cd {example directory}
# Assuming you have already run the simulation
paraFoam
```

Since all `Allrun` scripts create an empty `results.foam` file, when you run `paraFoam` under a case directory, it will open the case in ParaView. 
But the results will not be visible, you need to change the view option to display the U, p, and other fields.

![img.png](readme_image/img.png)

click on this bar and select the fields you want to display. U in this case.

now it will display the velocity field from top-down view, to see the inside of the geometry, you can use the clip filter.

![img_1.png](readme_image/img_1.png)

to view the result at a different time, you can use the time slider at the top of the window.

![img_2.png](readme_image/img_2.png)

The resulting visualization looks like this
![img_3.png](readme_image/img_3.png)

### Saving the results
You can save each wind velocity field as a .csv file by using paraView, or use openFoam's built-in command 
```bash
postProcess -func writeCellCentres
``` 
to postprocess the results by export each cell's center to a `C` file. the index of `C` will bijectionally map to the values in the `U` file in each time step folder.

Or, alternatively, you can use the paraView:

![img_4.png](readme_image/img_4.png)

![img_5.png](readme_image/img_5.png)

This will save all the wind velocity field and cell coordinate  at each time step as a .csv file in the `postProcessing` folder in the case directory.



## Known Issues

### Parallel computing issue
If your CPU has less than 6 cores, you need to change the `runParallel` to `runApplication` in the `Allrun` file in each example directory, otherwise the simulation may not run. 

Or change your available cores in the `decomposeParDict` file in the `system` folder in each example directory by changing `numberOfSubdomains  6` to your available cores.

### Storage issue
https://github.com/microsoft/WSL/issues/4699

If you are using WSL, the storage is limited to the 100GB, and once allocated, it cannot be freed.
to free up the storage after simulating large cases, we need to delete the old cases to free up the storage for windows.

First locate the WSL image in the windows file system
it should be in the following directory

`C:\Users\{username}\AppData\Local\Packages\CanonicalGroupLimited.Ubunto{hash}\LocalState\ext4.vhdx`

Then free up the storage by optimizing the image
```PowerShell
wsl --shutdown
optimize-vhd -Path {path to ext4.vhdx} -Mode full
```

### ParaView cannot be opened
If you cannot open ParaView using the command `paraFoam`:

1. **WSL users with segfault issues**: Use the Windows ParaView setup script (see "Setting up Windows ParaView for WSL" above). The WSL version of ParaView may segfault due to OpenGL issues.

2. **Unusual folder names**: Sometimes it's because of unusual folder names in the case folder. Delete any folders that are not the default OpenFOAM folder names and try again.

3. **results.foam file issues**: If OpenFOAM aborts with "invalid fileName results.foam", ensure the `results.foam` file is removed before running simulations. The `Allclean` script should handle this automatically.


### Allrun and Allclean cannot be executed
if you see
```text
./Allclean: line 3: $'\r': command not found
```
It is because the file is not in the correct format, change the file line separator to `LF` using any text editor.

**IMPORTANT:**
if you already ran the `Allrun` script in `CRLF` format, there will be a `results.foam` file with `LF` at the end of the file name, and it will cause OpenFoam to crash. 
Just remove it and run the `Allrun` script again in `LF` format.
