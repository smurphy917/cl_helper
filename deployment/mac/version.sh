#!/bin/sh
if [ -z "$1" ]
    then
        VERSION_FILE=$(cat config/version)
        VERSION_LINES=(${VERSION_FILE[@]})
        VERSION="${VERSION_LINES[0]}"
    else
        VERSION=$1
fi
echo $VERSION