#!/bin/sh
if [ -z "`diff -w $1 $2`" ]; then
	echo 1 > result
else
	echo -1 > result
fi
