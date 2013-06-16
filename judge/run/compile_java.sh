#!/bin/bash

# Java compile script based on the compile_java.sh in DOMJudge

SOURCE="$1"
MAINCLASS=""

#javac -d . "$SOURCE" &> log
#JAVAC="javac -J-Xmx80m -J-Xmx75m -d ."
JAVAC="javac -d ."
#ulimit -a
$JAVAC "$SOURCE" &> log
EXITCODE=$?
if [ "$EXITCODE" -ne 0 ]; then
	# Let's see if should have named the .java differently
	PUBLICCLASS=$(sed -n -e '/class .* is public, should be declared in a file named /{s/.*file named //;s/\.java.*//;p;q}' log)
	if [ -z "$PUBLICCLASS" ]; then
		echo 'No public classes found'
		cat log
		exit $EXITCODE
	fi
	echo "Info: renaming source to '$PUBLICCLASS.java'"
	cp "$SOURCE" "$PUBLICCLASS.java"
	$JAVAC "$PUBLICCLASS.java" &> log
	EXITCODE=$?
	[ "$EXITCODE" -ne 0 ] && exit $EXITCODE
fi

# Look for class that has the 'main' function:
for cn in $(find * -type f -regex '^.*\.class$' \
		| sed -e 's/\.class$//' -e 's/\//./'); do
	javap -public "$cn" \
	| grep -q 'public static void main(java.lang.String\[\])' \
	&& {
		if [ -n "$MAINCLASS" ]; then
			echo "Warning: found another 'main' in '$cn'"
		else
			echo "Info: using 'main' from '$cn'"
			MAINCLASS=$cn
		fi
	}
done
if [ -z "$MAINCLASS" ]; then
	echo "Error: no 'main' found in any class file."
	echo "Error: no 'main' found in any class file." >> log
	exit 1
fi

echo $MAINCLASS > mainclass.txt
zip binary.zip mainclass.txt *.class
mv binary.zip binary
rm mainclass.txt *.class

# Calculate Java program memlimit as MEMLIMIT - max. JVM memory usage:
#MEMLIMITJAVA=$(($MEMLIMIT - 300000))
#MEMLIMITJAVA=153600
#MEMLIMITJAVA=131072


#echo $MEMLIMIT $MEMLIMITJAVA

# Write executing script:
# Executes java byte-code interpreter with following options
# -Xmx: maximum size of memory allocation pool
# -Xrs: reduces usage signals by java, because that generates debug
#       output when program is terminated on timelimit exceeded.

#cat > $DEST <<EOF
##!/bin/sh
## Generated shell-script to execute java interpreter on source.
#exec java -Xrs -Xss8m -Xmx${MEMLIMITJAVA}k $MAINCLASS
#EOF

#chmod a+x $DEST

exit 0
