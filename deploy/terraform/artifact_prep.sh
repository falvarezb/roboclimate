#!/bin/bash

# https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425?permalink_comment_id=3945021
set -exuvo pipefail

function prepare_pkg() {
    lambda_function="$1"    
    if [ "$lambda_function" != "weather" ] && [ "$lambda_function" != "forecast" ]; then
        echo "resource must be one of 'weather' or 'forecast'"
        exit 1
    fi

    pkg_folder=${lambda_function}_pkg
    rm -rf "$pkg_folder"
    mkdir "$pkg_folder"
    pip install --target "$pkg_folder" -r "$ROBOCLIMATE_HOME"/lambda_requirements.txt
    cp "$ROBOCLIMATE_HOME"/roboclimate/"${lambda_function}"_spider.py "$ROBOCLIMATE_HOME"/roboclimate/common.py "$pkg_folder"
}

prepare_pkg "weather"