#!/bin/sh
CWD=$PWD
pushd `dirname $0` > /dev/null
SCRIPT_DIR=`pwd`
popd > /dev/null
if [[ $0 == *deploy.sh ]]
then
    cd "$SCRIPT_DIR"
elif [[ $0 == *build.sh ]]
then
    cd "$SCRIPT_DIR/../.."
fi

if [ -z "$VERSION" ]
then
    VERSION=$(. deployment/mac/version.sh)
fi
echo "Building CL Helper v$VERSION"
echo "$VERSION" > config/version
pyupdater build -F --windowed --app-version="$VERSION" mac.pyu.spec
cd $CWD