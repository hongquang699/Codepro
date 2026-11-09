#!/bin/bash
rustc -O "$1" -o "$2" 2> compile.log
