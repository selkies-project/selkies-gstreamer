
#!/bin/bah                                                                                                                                                                             
N=selkies-js-interposer-deb
GIT_TAG=$(git describe --tag)
TAG=latest
V=12

ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ] || [ "$ARCH" = "amd64" ]; then
    ARCH=amd64    
fi
#_debian${V}_${ARCH}

 docker build \
     --build-arg=DEBFULLNAME="Alex Diaz" \
     --build-arg=DEBEMAIL=alex@qbo.io \
     --build-arg=PKG_NAME=selkies-js-interposer \
     --build-arg=PKG_VERSION=${GIT_TAG#v} \
     --build-arg=DISTRIB_RELEASE=12 \
     -t $N:$TAG -f Dockerfile.debian_debpkg .

I=$(docker images $N:$TAG --format "{{.ID}}")
if [ ! -d dist ]; then
    mkdir dist
fi

#echo $I

if [ "$1" = "-c" ]; then
    rm -f ./dist/*
fi

(set -x; docker run -v $PWD/dist:/dist $I bash -c "cp /opt/selkies-js-interposer_${GIT_TAG#v}.tar.gz /dist/selkies-js-interposer_v${GIT_TAG#v}_debian${V}_${ARCH}.tar.gz")
(set -x; docker run -v $PWD/dist:/dist $I bash -c "cp /opt/selkies-js-interposer_${GIT_TAG#v}.deb /dist/selkies-js-interposer_v${GIT_TAG#v}_debian${V}_${ARCH}.deb")
