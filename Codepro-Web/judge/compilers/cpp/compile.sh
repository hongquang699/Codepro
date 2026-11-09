#!/bin/bash
SOURCE_FILE=$1
OUTPUT_BIN=$2
g++ -O3 -std=c++17 -Wall "$SOURCE_FILE" -o "$OUTPUT_BIN" 2> compile.log
exit $?
