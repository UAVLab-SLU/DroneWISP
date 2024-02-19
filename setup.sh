#!/usr/bin/env bash

# see if openfoam is installed, check if foamVersion runs
if ! command -v foamVersion &> /dev/null
then
    echo "OpenFOAM is not installed."
    echo "intalling OpenFOAM..."
    sudo apt-get update
    sudo sh -c "wget -O - http://dl.openfoam.org/gpg.key | apt-key add -"
    sudo add-apt-repository http://dl.openfoam.org/ubuntu
    sudo apt-get update
    sudo apt-get install openfoam10
    sudo apt-get install --only-upgrade openfoam10
    echo "source /opt/openfoam10/etc/bashrc" >> ~/.bashrc
    source ~/.bashrc
    echo "OpenFOAM installed."
fi
