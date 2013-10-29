#!/bin/bash
echo -3 > status
"$RUNSAFE" "$1" < "$2" > stdout 2> stderr && echo 1 > status
