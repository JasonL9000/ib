FROM debian

RUN apt update

RUN apt install -y build-essential \
    git \
    python \
    dos2unix \
    clang \
    gcc-mingw-w64 \
    vim \
    wine \
    zsh \
    curl \
    wget

# install python testing tools
RUN apt install -y python-setuptools python-dev
RUN easy_install pip
RUN pip install --upgrade virtualenv
RUN pip install pytest pytest-xdist pytest-cov

RUN dpkg --add-architecture i386 && apt update && apt install -y wine32
RUN wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true
RUN echo "export HISTFILE=/root/out/.zsh_history" >> ~/.zshrc

ENV PATH "$PATH:/root/ib"
WORKDIR '/root/ib'

ADD . /root/ib

# Build all the examples
RUN ./scripts/build_all_on_linux.sh

# Run the unit tests
RUN ./scripts/run_tests.sh
