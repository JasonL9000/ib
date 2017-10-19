if not exist ..\out mkdir ..\out
git config user.name > ..\out\user.name.txt
git config user.email > ..\out\user.email.txt
set /p GIT_USER_NAME=<..\out\user.name.txt
set /p GIT_USER_EMAIL=<..\out\user.email.txt

docker run -ti ^
  -e "GIT_USER_EMAIL:%GIT_USER_EMAIL%" ^
  -e "GIT_USER_NAME:%GIT_USER_NAME%" ^
  -v %cd%\..\out:/root/out ^
  -v %cd%:/root/ib ^
  ib /bin/bash scripts/build_all_on_linux.sh
