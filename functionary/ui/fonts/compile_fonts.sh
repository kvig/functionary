#!/bin/bash

if ! which npm &>/dev/null; then
    printf "Make sure you have npm installed. Get the latest with:\n"
    printf "\tcurl -sL https://deb.nodesource.com/setup_18.x > setupNode.sh\n"
    printf "\tchmod +x setupNode.sh\n"
    printf "\tsudo ./setupNode.sh\n"
    printf "\tapt-get install nodejs\n"
fi

# Make a working directory and find the directory of this script
TMP_DIR=$(mktemp -d)
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "Script is in:   ${SCRIPT_DIR}"
echo "Downloading to: ${TMP_DIR}"
echo

echo "Changing to ${SCRIPT_DIR}"
pushd "${SCRIPT_DIR}" &> /dev/null || exit

echo "Copying required files"
cp subset_font.js "${TMP_DIR}/"

echo
echo "Changing to ${TMP_DIR}"
pushd "${TMP_DIR}" &> /dev/null|| exit

# Download the Playball font for the F logo
echo "Downloading Playball font"
wget -q https://github.com/google/fonts/blob/main/ofl/playball/Playball-Regular.ttf?raw=true -O Playball-Regular.ttf
if [ $? -ne 0 ]; then
    echo "Failed to download and unpack Bootstrap ${BOOTSTRAP_VERSION}"
    exit 1
fi
echo "Subsetting font"
npm install --silent fontkit subset-font
node subset_font.js "${SCRIPT_DIR}/../static/webfonts/Functionary_Playball.woff2"
if [ $? -ne 0 ]; then
    echo "Failed to subset font"
    exit 2
fi

# Exit from $TMP_DIR
echo
echo "Leaving ${TMP_DIR}"
popd &> /dev/null || exit

# Cleanup the extra files
echo "Cleaning up ${TMP_DIR}"
rm -rf "${TMP_DIR:?}/"

# Exit from $SCRIPT_DIR
echo
echo "Leaving ${SCRIPT_DIR}"
popd &> /dev/null || exit