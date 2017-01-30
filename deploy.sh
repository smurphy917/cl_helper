#!/bin/sh
export PYU_AWS_ID='AKIAIHVLDAEIBMV5WIQQ'
export PYU_AWS_SECRET='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'
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