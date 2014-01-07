#!/bin/bash
# Usage: ./run_boxed.sh <time> <memory> <safe run command> <program> [program args]
# NOTE: This should be run as the user who runs the program.

export RUNSAFE=$3
ulimit -t $1
if [ $2 != 0 ]; then ulimit -u 10 -v $2; else ulimit -u 1000; fi
ulimit -f 4096
ulimit -s unlimited
timeout $1 ${@:4}
