# Base image with MiniZinc installed
FROM minizinc/minizinc:latest

# Avoid Python parallelism
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OPENBLAS_NUM_THREADS=1
ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /CDMO

# Install Python 3.11 and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    wget \
    unzip \
    ca-certificates \
    build-essential \
    coinor-cbc \
    glpk-utils \
    libglpk40 \
    libedit2 \
    libtinfo6 \
    libc6 \
    libstdc++6 \
    libgl1 \
    libegl1 \
    libosmesa6 \
    libfontconfig1 \
    libfreetype6 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    libxrandr2 \
    libxi6 \
    libxfixes3 \
    libgpg-error0 \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends python3.11 python3.11-venv python3.11-distutils \
    && wget https://bootstrap.pypa.io/get-pip.py -O /tmp/get-pip.py \
    && python3.11 /tmp/get-pip.py \
    && rm -rf /var/lib/apt/lists/* /tmp/get-pip.py

# Make python3 point to python3.11
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Copy project files
COPY . /CDMO

# Install Python requirements (including amplpy)
RUN pip install --no-cache-dir -r requirements.txt

# Install licensed solvers inside Docker using amplpy modules
# License key is read from environment variable
ARG AMPL_LICENSE_UUID
ENV AMPL_LICENSE_UUID=${AMPL_LICENSE_UUID}
RUN python -m amplpy.modules install gurobi \
    && python -m amplpy.modules install cplex \
    && python -m amplpy.modules install scip \
    && python -m amplpy.modules activate $AMPL_LICENSE_UUID

# Volumes for code and results
VOLUME ["/CDMO/res"]
VOLUME ["/CDMO/source"]

# Development-friendly entrypoint
ENTRYPOINT ["/bin/bash"]
