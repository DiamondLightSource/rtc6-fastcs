#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

cd "$SCRIPT_DIR/src/rtc6_fastcs/bindings"
rm -rf build
mkdir -p build
cd build
cmake ..
make
cd "$SCRIPT_DIR"

# Copy the newly built .so file if it was output to the wrong location
if [ -f "/workspace/src/rtc6_fastcs/bindings/rtc6_bindings.cpython-311-x86_64-linux-gnu.so" ]; then
    cp /workspace/src/rtc6_fastcs/bindings/rtc6_bindings.cpython-311-x86_64-linux-gnu.so \
       "$SCRIPT_DIR/src/rtc6_fastcs/bindings/rtc6_bindings.cpython-311-x86_64-linux-gnu.so"
fi

pip install -e .
pybind11-stubgen rtc6_fastcs.bindings.rtc6_bindings -o src

# Copy the generated .pyi from build dir to the correct location
if [ -f "src/rtc6_fastcs/bindings/build/src/rtc6_fastcs/bindings/rtc6_bindings.pyi" ]; then
    cp src/rtc6_fastcs/bindings/build/src/rtc6_fastcs/bindings/rtc6_bindings.pyi \
       src/rtc6_fastcs/bindings/rtc6_bindings.pyi
fi

ruff format .
