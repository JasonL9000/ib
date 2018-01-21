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

RUN git clone https://github.com/JasonL9000/ib.git /root/ib
RUN dpkg --add-architecture i386 && apt update && apt install -y wine32
RUN wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true
RUN echo "export HISTFILE=/root/out/.zsh_history" >> ~/.zshrc
ENV PATH "$PATH:/root/ib"
WORKDIR '/root/ib'
