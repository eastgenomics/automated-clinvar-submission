# Use the Nextflow base image
FROM nextflow/nextflow:22.10.3

# Install dependencies
RUN yum update -y && \
    yum groupinstall -y "Development Tools" && \
    yum install -y \
    bzip2-devel \
    openssl-devel \
    libffi-devel \
    wget \
    zlib-devel \
    ncurses-devel \
    sqlite-devel \
    readline-devel \
    tk-devel \
    gdbm-devel \
    db4-devel \
    libpcap-devel \
    xz-devel \
    expat-devel \
    openssl11 \
    make \
    bzip2 \
    nano \
    git && \
    yum clean all

# Install pyenv and python 3.10.10
RUN yum swap openssl-devel openssl11-devel -y
RUN git clone https://github.com/pyenv/pyenv.git /pyenv
ENV PYENV_ROOT /pyenv
RUN /pyenv/bin/pyenv install 3.10.10
RUN eval "$(/pyenv/bin/pyenv init -)" && /pyenv/bin/pyenv local 3.10.10

# Set the environment variables for pyenv
RUN echo 'export PATH="/pyenv/bin:$PATH"' >> ~/.bash_profile && \
    echo 'export PYENV_ROOT="/pyenv"' >> ~/.bash_profile && \
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile && \
    echo 'eval "$(pyenv init -)"' >> ~/.bash_profile && \
    source ~/.bash_profile && \
    echo 'export PYENV_ROOT="/pyenv"' >> ~/.bashrc && \
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
    source ~/.bashrc
# Export flags for openssl11 and set the temporary directory
RUN exec "$SHELL" && \
    export CFLAGS=$(pkg-config --cflags openssl11) && \
    export LDFLAGS=$(pkg-config --libs openssl11) && \
    mkdir -p ~/tmp && \
    export TMPDIR=~/tmp

# Global enable python 3.10.10 and install the variant_workbook_parser
RUN /pyenv/bin/pyenv global 3.10.10 && \
    /pyenv/bin/pyenv rehash && \
    git clone https://github.com/eastgenomics/variant_workbook_parser.git /variant_workbook_parser && \
    cd /variant_workbook_parser && \
    git checkout main && \
    git pull && \
    /pyenv/versions/3.10.10/bin/python -m ensurepip && \
    /pyenv/versions/3.10.10/bin/python -m pip install --upgrade pip && \
    /pyenv/versions/3.10.10/bin/python -m pip install -r /variant_workbook_parser/requirements.txt

# copy the main.nf file to the container
COPY . /home/

RUN /pyenv/versions/3.10.10/bin/python -m pip install -r /home/requirements.txt

# Specify the entrypoint to ensure the virtual environment is activated
# production testing
#ENTRYPOINT ["nextflow", "run", "/home/main.nf", "-c", "/home/configurations/test_config_20240821.txt"]
# local testing
ENTRYPOINT ["nextflow", "run", "/home/main.nf", "-c", "/home/configurations/configuration_test.txt"]
