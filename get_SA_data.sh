#!/bin/bash
set -x

_MY_SCRIPT="${BASH_SOURCE[0]}"
BASEDIR=$(cd "$(dirname "$_MY_SCRIPT")" && pwd)
_UNAME_OUT=$(uname -s)
DATA="${BASEDIR}/data"

# Prepare the data
mkdir $DATA

# Get the South Africa Municipal Demarcation Board data
# The gdb file for 2016
wget -nc -O "${DATA}/mdb2016.zip" "https://www.arcgis.com/sharing/rest/content/items/cfddb54aab5f4d62b2144d80d49b3fdb/data"
[ ! -d "${DATA}/MDBWard2016.gdb" ] && unzip -o -d "${DATA}" "${DATA}/mdb2016.zip"

# The gdb file for 2011
wget -nc -O "${DATA}/mdb2011.zip" "https://www.arcgis.com/sharing/rest/content/items/c34ba1c16a9d4797a32ca4e7755f5ded/data"
[ ! -d "${DATA}/MDBWard2011.gdb" ] \
  && unzip -o -d "${DATA}" "${DATA}/mdb2011.zip" \
  && mv "${DATA}/MDBDistrictMunicipalBoundary2011.gdb" "${DATA}/MDBWard2011.gdb"

# The gdb file for 2009
wget -nc -O "${DATA}/mdb2009.zip" "https://www.arcgis.com/sharing/rest/content/items/de335c384e694439be60ae14e97d169e/data"
[ ! -d "${DATA}/MDBWard2009.gdb" ] \
  && unzip -o -d "${DATA}" "${DATA}/mdb2009.zip" \
  && mv "${DATA}/MDBDistrictMunicipalBoundary2009.gdb" "${DATA}/MDBWard2009.gdb"

# South Africa geonames data
wget -nc -O "${DATA}/ZA.zip" "https://download.geonames.org/export/dump/ZA.zip" \
  && unzip -o -d "${DATA}" "${DATA}/ZA.zip" \
  && mv "${DATA}/readme.txt" "${DATA}/geonames_readme.txt" \
  && mv "${DATA}/ZA.txt" "${DATA}/geonames.tsv"

# Feature code lookup data
wget -nc -O "${DATA}/geonames_features.tsv" "https://download.geonames.org/export/dump/featureCodes_en.txt"

# Postal codes
wget -nc -O "${DATA}/postal_codes.zip" "https://download.geonames.org/export/zip/ZA.zip" \
  && unzip -o "${DATA}/postal_codes.zip" -d "${DATA}/" \
  && mv "${DATA}/readme.txt" "${DATA}/postal_codes_readme.txt" \
  && mv "${DATA}/ZA.txt" "${DATA}/postal_codes.tsv"
