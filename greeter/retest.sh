#!/bin/bash

echo "removing old version"
sudo rm -r /opt/lightdm-oauth-greeter
echo "copying new version"
sudo cp -r lightdm-oauth-greeter /opt/
echo "copying greeter desktop file"
sudo cp /opt/lightdm-oauth-greeter/lightdm-oauth-greeter.desktop /usr/share/xgreeters/

lightdm -c test.conf --test-mode --debug
