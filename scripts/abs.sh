DIR=$(echo "${1%/*}")
(cd "$DIR" && echo "$(pwd -P)")
