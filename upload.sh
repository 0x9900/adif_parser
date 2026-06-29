#!/bin/bash
set -e

rm -fr dist
python3 -m build
python3 -m twine upload dist/*
