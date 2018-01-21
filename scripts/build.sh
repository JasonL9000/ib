DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
docker build -t ib $($DIR/abs.sh $DIR/../)
