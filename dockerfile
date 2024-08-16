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


RUN yum swap openssl-devel openssl11-devel -y
RUN git clone https://github.com/pyenv/pyenv.git /pyenv
ENV PYENV_ROOT /pyenv
RUN /pyenv/bin/pyenv install 3.10.10
RUN eval "$(/pyenv/bin/pyenv init -)" && /pyenv/bin/pyenv local 3.10.10

RUN echo 'export PATH="/pyenv/bin:$PATH"' >> ~/.bash_profile && \
    echo 'export PYENV_ROOT="/pyenv"' >> ~/.bash_profile && \
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile && \
    echo 'eval "$(pyenv init -)"' >> ~/.bash_profile && \
    source ~/.bash_profile && \
    echo 'export PYENV_ROOT="/pyenv"' >> ~/.bashrc && \
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
    source ~/.bashrc
RUN exec "$SHELL" && \
    export CFLAGS=$(pkg-config --cflags openssl11) && \
    export LDFLAGS=$(pkg-config --libs openssl11) && \
    mkdir -p ~/tmp && \
    export TMPDIR=~/tmp
RUN /pyenv/bin/pyenv install 3.10.4 && \
    /pyenv/bin/pyenv versions && \
    /pyenv/bin/pyenv global 3.10.4 && \
    /pyenv/bin/pyenv rehash && \
    git clone --depth 1 --branch $(git ls-remote --tags --refs --sort="v:refname" https://github.com/eastgenomics/variant_workbook_parser.git | tail -n1 | sed 's/.*\///') \
    https://github.com/eastgenomics/variant_workbook_parser.git /variant_workbook_parser && \
    /pyenv/versions/3.10.4/bin/python -m ensurepip && \
    /pyenv/versions/3.10.4/bin/python -m pip install --upgrade pip && \
    /pyenv/versions/3.10.4/bin/python -m pip install -r /variant_workbook_parser/requirements.txt


# Copy env_file.txt to the container
COPY env_file.txt /env_file.txt

# Copy configuration.txt to the container
COPY configurations/configuration_test.txt /configuration.txt

# copy the main.nf file to the container
COPY ./ /home/

# Set environment variables from env_file.txt
ENV $(cat /env_file.txt | xargs)

# Specify the entrypoint to ensure the virtual environment is activated
ENTRYPOINT ["/bin/bash"]
