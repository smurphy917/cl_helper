VERSION_FILE=$(cat config/version)
VERSION_LINES=(${VERSION_FILE[@]})
VERSION="${VERSION_LINES[0]}"
echo $VERSION
