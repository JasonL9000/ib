docker run -ti \
  -v $(pwd)/../out:/root/out \
  -v $(pwd):/root/ib \
  ib /bin/bash scripts/build_all_on_linux.sh
