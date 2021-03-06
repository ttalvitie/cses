#!/bin/bash
BINARY="$1"
INPUT="$2"
cp "$BINARY" binary.zip
unzip binary.zip
rm binary.zip
MAINCLASS=`cat mainclass.txt`

echo -3 > status
"$RUNSAFE" java -Xmx150m $MAINCLASS < "$INPUT" > stdout 2> stderr && echo 1 > status
rm *.class mainclass.txt
exit 0
