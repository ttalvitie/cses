#!/bin/bash
echo -3 > status
"$1" < "$2" > stdout 2> stderr && echo 1 > status
