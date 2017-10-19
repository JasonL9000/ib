FROM debian

RUN apt update
RUN apt install -y build-essential
RUN apt install -y git
RUN apt install -y python
RUN git clone https://github.com/JasonL9000/ib.git /root/ib
RUN apt install -y dos2unix
RUN apt install -y clang
RUN apt install -y gcc-mingw-w64
RUN apt install -y vim
RUN apt install -y wine
RUN dpkg --add-architecture i386 && apt update && apt install -y wine32
RUN apt install -y zsh
RUN apt install -y curl
RUN apt install -y wget
RUN wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh || true
RUN echo "export HISTFILE=/root/out/.zsh_history" >> ~/.zshrc
ENV PATH "$PATH:/root/ib"
WORKDIR '/root/ib'
