FROM debian

RUN apt update
RUN apt install -y build-essential
RUN apt install -y git
RUN apt install -y python
RUN git clone https://github.com/JasonL9000/ib.git /root/ib
RUN apt install -y dos2unix
RUN apt install -y clang
RUN apt install -y gcc-mingw-w64
ENV PATH "$PATH:/root/ib"
WORKDIR '/root/ib'
