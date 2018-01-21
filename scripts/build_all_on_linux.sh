DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)

CONFIGS="\
  clang_debug \
  clang_asan \
  clang_release \
  gcc_debug \
  gcc_asan \
  gcc_release \
"

WIN_CONFIGS="\
  mingw_64x_debug \
  mingw_64x_release \
  mingw_32x_debug \
  mingw_32x_release \
"

for cfg_name in $CONFIGS; do
  # build and execute
  echo "building $cfg_name"
  ib --cfg cfgs/$cfg_name examples/hello $@
done

for cfg_name in $WIN_CONFIGS; do
  echo "building $cfg_name"
  ib --cfg cfgs/$cfg_name examples/hello.exe $@
  ib --cfg cfgs/$cfg_name examples/basic.exe $@
  ib --cfg cfgs/$cfg_name examples/win_hello.exe $@
  ib --cfg cfgs/$cfg_name examples/win_opengl.exe $@
done
echo "built to ../out"
