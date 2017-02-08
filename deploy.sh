#!/bin/sh
while IFS='=' read var val
do
    export "$var"="$val"
done <<< "$(cat id.s3)"
CWD=$PWD
pushd `dirname $0` > /dev/null
SCRIPT_DIR=`pwd`
popd > /dev/null
cd "$SCRIPT_DIR"
VERSION=$(. deployment/mac/version.sh)
echo "Building CL Helper v$VERSION"
BUILD_OUTPUT=$(. deployment/mac/build.sh)
pyupdater pkg --process --sign
pyupdater upload --service s3
cd $CWD
echo "Deployment complete for version $VERSION"