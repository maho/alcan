#!/bin/bash

set -ex

pip install --upgrade pip
pip install --upgrade setuptools
pip install "cython==0.25.2" pillow


test -n "$SKIP_CYMUNK" || pip install git+https://github.com/tito/cymunk
test -n "$SKIP_KIVY" || pip install git+git://github.com/kivy/kivy@master


pip install pyyaml pyinstaller
