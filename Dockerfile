# Use the official Python image with the specified version
FROM python:3.10

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

# Install OpenFOAM 10
RUN sudo apt-get update && \
    wget -q -O - http://dl.openfoam.com/add-debian-repo.sh | bash && \
    apt-get update && \
    apt-get install -y openfoam-default && \
    echo "source /usr/lib/openfoam/openfoam/etc/bashrc" >> ~rwds/.bashrc && \
    echo "export OMPI_MCA_btl_vader_single_copy_mechanism=none" >> ~rwds/.bashrc

# Install Python dependencies
COPY python/requirements.txt .
RUN sudo -E pip install --no-cache-dir -r requirements.txt

# Switch to the new user "rwds"
USER rwds
RUN . ~/.bashrc

# Set the working directory
WORKDIR /home/rwds


COPY python/ .

# Change ownership
RUN sudo chown -R rwds:rwds /home/rwds/

# Set read, write, and execute permissions for user and group
RUN sudo chmod -R 770 /home/rwds/

# Documents/AirSim
RUN mkdir -p /home/rwds/Documents/AirSim/report/

EXPOSE 5001

ENV IN_DOCKER Yes

CMD ["python", "cfd_server.py", "-h", "0.0.0.0", "-p", "5001"]
