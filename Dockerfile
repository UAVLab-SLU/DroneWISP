# Use the official Python image with the specified version
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive



ENV TZ=America/Chicago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Update and install Python and pip
RUN apt-get update

RUN apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*


# Set environment variables to avoid some common issues with running Docker as root
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install essential packages
RUN apt-get update && apt-get install -y ssh curl nano git htop build-essential software-properties-common ca-certificates sudo wget gnupg

# Update the package list
RUN apt-get update && apt-get install -y --no-install-recommends

# Create a new user "rwds" and add it to the sudoers list
RUN adduser --disabled-password --gecos '' rwds && \
    adduser rwds sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Add OpenFOAM repository and key, and install OpenFOAM
RUN sh -c "wget -O - http://dl.openfoam.org/gpg.key | apt-key add -" \
    && add-apt-repository http://dl.openfoam.org/ubuntu \
    && apt-get update \
    && apt-get install -y openfoam10 \
    && apt-get install --only-upgrade -y openfoam10

# Set up environment for OpenFOAM
RUN echo "source /opt/openfoam10/etc/bashrc" >> /etc/bash.bashrc

# Install Python dependencies
COPY python/requirements.txt .
RUN sudo -E pip install --no-cache-dir -r requirements.txt

# Switch to the new user "rwds"
USER rwds
RUN . ~/.bashrc

# Set the working directory
WORKDIR /home/rwds

RUN echo "source /opt/openfoam10/etc/bashrc" >> ~/.bashrc && \
    echo "source /opt/openfoam10/bin/tools/RunFunctions" >> ~/.bashrc && \
    echo "source /opt/openfoam10/bin/tools/CleanFunctions" >> ~/.bashrc



COPY python/ .

# Change ownership
RUN sudo chown -R rwds:rwds /home/rwds/

# Set read, write, and execute permissions for user and group
RUN sudo chmod -R 770 /home/rwds/

# Documents/AirSim
RUN mkdir -p /home/rwds/Documents/AirSim/report/

EXPOSE 5001

ENV IN_DOCKER Yes

CMD ["python3", "cfd_server.py", "-h", "0.0.0.0", "-p", "5001"]
