#!/bin/sh
# Usage: ./run_boxed.sh <time> <memory> <program> [program args]
# NOTE: This should be run as the user who runs the program.

ulimit -u 10 -t $1 -v $2
timeout $1 ${@:3}
