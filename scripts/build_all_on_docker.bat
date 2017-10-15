docker run -ti ^
  -v %cd%\..\out:/root/out ^
  -v %cd%:/root/ib ^
  ib /bin/bash scripts/build_all_on_linux.sh
