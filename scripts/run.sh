docker run -ti \
  -v $(pwd)/../out:/root/out \
  -v $(pwd):/root/ib \
  ib /bin/sh -c "dos2unix /root/ib /root/ib && bash"