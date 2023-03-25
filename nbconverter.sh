#!/bin/sh

# jupyter nbconvert --to html --template hidecode my_notebook.ipynb

jupyter nbconvert --ExecutePreprocessor.kernel_name=python3  --no-input --to html --execute ./roboclimate.ipynb
cp ./roboclimate.html /usr/share/nginx/html/roboclimate/index.html