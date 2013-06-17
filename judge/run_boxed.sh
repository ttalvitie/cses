#!/bin/bash
# Usage: ./run_boxed.sh <time> <memory> <program> [program args]
# NOTE: This should be run as the user who runs the program.

ulimit -t $1
if [ $2 != 0 ]; then ulimit -u 10 -v $2; else ulimit -u 1000; fi
ulimit -f 10000
timeout $1 ${@:3}
