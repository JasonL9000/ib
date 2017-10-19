mkdir -p ../out
GIT_USER_NAME=$(git config user.name)
GIT_USER_EMAIL=$(git config user.email)

docker run -ti \
  -e "GIT_USER_NAME=${GIT_USER_NAME}" \
  -e "GIT_USER_EMAIL=${GIT_USER_EMAIL}" \
  -v $(pwd)\..\out:/root/out \
  -v $(pwd):/root/ib \
  ib /bin/sh -c "scripts/start.sh && zsh"
