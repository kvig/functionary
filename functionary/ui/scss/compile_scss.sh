#!/bin/bash

if ! which npm &>/dev/null; then
    printf "Make sure you have npm installed. Get the latest with:\n"
    printf "\tcurl -sL https://deb.nodesource.com/setup_18.x > setupNode.sh\n"
    printf "\tchmod +x setupNode.sh\n"
    printf "\tsudo ./setupNode.sh\n"
    printf "\tapt-get install nodejs\n"
fi

export BOOTSTRAP_VERSION="5.2.3"

# Make a working directory and find the directory of this script
TMP_DIR=$(mktemp -d)
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo "Script is in:   ${SCRIPT_DIR}"
echo "Downloading to: ${TMP_DIR}"
echo

echo "Changing to ${SCRIPT_DIR}"
pushd "${SCRIPT_DIR}" &> /dev/null || exit

# Install sass into the directory custom.scss is in, the /tmp
# directory may not have execute set on it
echo "Installing sass"
npm install --silent sass
cp custom.scss "${TMP_DIR}/"

echo
echo "Changing to ${TMP_DIR}"
pushd "${TMP_DIR}" &> /dev/null|| exit

# Download the specific version of BOOTSTRAP above and move the files
# into the local directory
echo "Downloading and extracting bootstrap"
wget -q https://github.com/twbs/bootstrap/archive/v${BOOTSTRAP_VERSION}.zip && unzip -q -d . v${BOOTSTRAP_VERSION}.zip
if [ $? -ne 0 ]; then
    echo "Failed to download and unpack Bootstrap ${BOOTSTRAP_VERSION}"
    exit 1
fi
mv bootstrap-${BOOTSTRAP_VERSION}/scss/* .
rm -rf ./v${BOOTSTRAP_VERSION}.zip ./bootstrap-${BOOTSTRAP_VERSION}
if [ $? -ne 0 ]; then
    echo "Unable to move the bootstrap files"
    exit 2
fi
rm -rf ./v${BOOTSTRAP_VERSION}.zip ./bootstrap-${BOOTSTRAP_VERSION}
if [ $? -ne 0 ]; then
    echo "WARNING: Unable to cleanup the downloaded Bootstrap files"
fi

# Make sure sass is installed and run it
echo "Compiling CSS"
"${SCRIPT_DIR}/node_modules/.bin/sass" custom.scss "${SCRIPT_DIR}/../static/css/custom_bootstrap.css"
if [ $? -ne 0 ]; then
    echo "Failed to generate the custom css!"
    exit 3
fi

# Exit from $TMP_DIR
echo
echo "Leaving ${TMP_DIR}"
popd &> /dev/null || exit

# Cleanup the extra files
echo "Cleaning up node_modules and ${TMP_DIR}"
rm -rf ./node_modules package-lock.json package.json
rm -rf "${TMP_DIR:?}/"

# Exit from $SCRIPT_DIR
echo
echo "Leaving ${SCRIPT_DIR}"
popd &> /dev/null || exit