#!/bin/sh
# as simple as that:

echo "Building $1 version $2"
echo "======================"

sed -i -e "s/define ShortName \"inkscape\-.*\"\$/define ShortName \"$1\"/" installer.nsi # installer_de.nsi
sed -i -e "s/define AppVersion \"v.*\"\$/define AppVersion \"v$2\"/"       installer.nsi # installer_de.nsi

cp ../../3d-projection.py .
cp ../../3d-projection.inx .
# cp ../../3d-projection_.inx .

makensis installer.nsi
# makensis installer_de.nsi

