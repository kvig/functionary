#!/bin/bash

# Make sure you have npm installed. Get the latest with:
# curl -sL https://deb.nodesource.com/setup_18.x > setupNode.sh
# chmod +x setupNode.sh
# sudo ./setupNode.sh
# apt-get install nodejs

export BOOTSTRAP_VERSION="5.2.3"

# Download the specific version of BOOTSTRAP above and move the files
# into the local directory
wget https://github.com/twbs/bootstrap/archive/v${BOOTSTRAP_VERSION}.zip && unzip -d . v${BOOTSTRAP_VERSION}.zip
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
npm install sass
./node_modules/.bin/sass custom.scss ../static/css/custom.css
if [ $? -ne 0 ]; then
    echo "Failed to generate the custom css!"
    exit 3
fi

# Cleanup the extra files
echo "Removing .scss files"
/bin/ls -1 ./*.scss | grep -v custom.scss | xargs rm
echo "Removing directories"
find . -type d -regex "^\./[a-z].*$" -exec rm -rf {} \;
echo "Removing npm files"
rm package-lock.json package.json
