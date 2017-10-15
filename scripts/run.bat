docker run -ti ^
  -v %cd%\..\out:/root/out ^
  -v %cd%:/root/ib ^
  ib /bin/sh -c "dos2unix /root/ib /root/ib && bash"