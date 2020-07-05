#!/bin/sh

jupyter nbconvert --ExecutePreprocessor.kernel_name=python3  --no-input --to html --execute ./notebook.ipynb
cp ./notebook.html /usr/share/nginx/html/roboclimate/index.html