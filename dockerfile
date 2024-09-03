# Use the Nextflow base image
FROM nextflow/nextflow:22.10.3

# Install dependencies
RUN yum groupinstall -y "Development Tools" && \
    yum install -y \
    bzip2-devel \
    libffi-devel \
    openssl11-devel \
    wget \
    make \
    bzip2 \
    git && \
    yum -y clean all && \
    rm -fr /var/cache && \
    rm -rf /var/cache/yum

# Set the environment variables
ENV PYENV_ROOT /pyenv
ENV SLACK_WEBHOOK_TEST=default
ENV SLACK_WEBHOOK_LOGS=default
ENV SLACK_WEBHOOK_ALERTS=default

# Install pyenv and python 3.10.10
RUN git clone --depth 1 https://github.com/pyenv/pyenv.git /pyenv && \
    /pyenv/bin/pyenv install 3.10.10 && \
    eval "$(/pyenv/bin/pyenv init -)" && /pyenv/bin/pyenv local 3.10.10

# Set the environment variables for pyenv
RUN echo 'export PATH="/pyenv/bin:$PATH"' >> ~/.bash_profile && \
    echo 'export PYENV_ROOT="/pyenv"' >> ~/.bash_profile && \
    echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile && \
    echo 'eval "$(pyenv init -)"' >> ~/.bash_profile && \
    source ~/.bash_profile && \
    echo 'export PYENV_ROOT="/pyenv"' >> ~/.bashrc && \
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc && \
    echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
    source ~/.bashrc && \
    exec "$SHELL" && \
    export CFLAGS=$(pkg-config --cflags openssl11) && \
    export LDFLAGS=$(pkg-config --libs openssl11) && \
    mkdir -p ~/tmp && \
    export TMPDIR=~/tmp

COPY . /home/

# Clone the variant_workbook_parser repository and install its dependencies
RUN git clone --depth 1 --branch $(git ls-remote --tags --refs --sort="v:refname" https://github.com/eastgenomics/variant_workbook_parser.git | tail -n1 | sed 's/.*\///') \
    https://github.com/eastgenomics/variant_workbook_parser.git /variant_workbook_parser && \
    /pyenv/versions/3.10.10/bin/python -m pip install -r /variant_workbook_parser/requirements.txt && \
    /pyenv/versions/3.10.10/bin/python -m pip install -r /home/requirements.txt && \
    rm -rf /var/cache/yum
