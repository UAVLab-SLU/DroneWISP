# Use the official Python image with the specified version
FROM python:3.10

# Set environment variables to avoid some common issues with running Docker as root
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install essential packages
RUN apt-get update
RUN apt-get install -y ssh
RUN apt-get install -y curl
RUN apt-get install -y nano
RUN apt-get install -y git
RUN apt-get install -y htop
RUN apt-get install -y build-essential
RUN apt-get install -y software-properties-common
RUN apt-get install ca-certificates
RUN apt-get update

# Update the package list
RUN apt-get update && \
    apt-get install -y --no-install-recommends sudo wget gnupg software-properties-common


# Create a new user "rwds" and add it to the sudoers list
RUN adduser --disabled-password --gecos '' rwds && \
    adduser rwds sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers


# Install OpenFOAM 10
RUN sudo apt-get update
RUN wget -q -O - http://dl.openfoam.com/add-debian-repo.sh | bash
RUN apt-get update
RUN apt-get install -y openfoam-default
RUN echo "source /usr/lib/openfoam/openfoam/etc/bashrc" >> ~rwds/.bashrc
RUN echo "export OMPI_MCA_btl_vader_single_copy_mechanism=none" >> ~rwds/.bashrc

# Install Python dependencies
COPY python/requirements.txt .
RUN sudo -E pip install --no-cache-dir -r requirements.txt

# Switch to the new user "rwds"
USER rwds
RUN . ~/.bashrc

# Set the working directory
WORKDIR /home/rwds


COPY python/ .
# Documents/AirSim
RUN mkdir -p /home/rwds/Documents/AirSim/report/

EXPOSE 5001

ENV IN_DOCKER Yes

CMD ["python", "cfd_server.py", "-h", "0.0.0.0", "-p", "5001"]
