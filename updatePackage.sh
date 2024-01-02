#!/bin/bash


# Upload package note:
# Generate token and set file -> $HOME/.pypirc
#
# [pypi]
#   username = __token__
#   password = pypi-XXXXXXXX
#

# Generate package
./setup.py sdist bdist_wheel

# upload to pypi
twine upload dist/*
