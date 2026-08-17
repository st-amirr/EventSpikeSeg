FROM pytorch/pytorch:2.2.2-cuda11.8-cudnn8-runtime

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ghdl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/eventspikeseg
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir '.[dev,rtl]'
RUN python -c "import hdf5plugin; print('DSEC HDF5 filters:', hdf5plugin.PLUGINS_PATH)"

WORKDIR /workspace
