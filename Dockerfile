# Use the official base image
FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Chicago

# Set timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Update system and install necessary packages
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ssh \
    curl \
    nano \
    git \
    htop \
    build-essential \
    software-properties-common \
    ca-certificates \
    sudo \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Create a new user "wisp" and add it to the sudoers list
RUN adduser --disabled-password --gecos '' wisp && \
    adduser wisp sudo && \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Switch to the new user "wisp"
USER wisp

# Set environment variables to avoid some common issues with running Docker as root
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /home/wisp

# Add OpenFOAM repository and key, and install OpenFOAM
RUN sudo sh -c "wget -O - http://dl.openfoam.org/gpg.key | apt-key add -" && \
    sudo add-apt-repository http://dl.openfoam.org/ubuntu && \
    sudo apt-get update && \
    sudo apt-get install -y openfoam10 && \
    sudo apt-get install --only-upgrade -y openfoam10

# Set up environment for OpenFOAM
RUN echo "source /opt/openfoam10/etc/bashrc" >> /home/wisp/.bashrc

# Install Python dependencies
COPY --chown=wisp:wisp python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=wisp:wisp python/ .

# Create directories and set permissions

# Set necessary environment variable
ENV IN_DOCKER Yes

# Expose necessary port
EXPOSE 5001

# Set the command to run the application
CMD ["python3", "cfd_server.py","--preprocess_mode", "kd_tree", "--host", "0.0.0.0", "--port", "5001"]
