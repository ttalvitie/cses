class Result:
	PENDING = -101
	JUDGING = -100
	COMPILE_ERROR = -2
	WRONG_ANSWER = -1
	INTERNAL_ERROR = -9001
	ACCEPTED = 1

names = filter(lambda x: x[0]!='_', dir(Result))
numNames = dict([(getattr(Result,i),i) for i in names])

def toString(result):
	if result not in numNames:
		return str(result)
	return numNames[result]
