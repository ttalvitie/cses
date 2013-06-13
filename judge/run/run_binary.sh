#!/bin/sh
"$1" < "$2" > stdout 2> stderr
echo 1 > status
