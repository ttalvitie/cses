class Result:
	INTERNAL_ERROR = -9001
	PENDING = -101
	JUDGING = -100
	COMPILE_ERROR = -10
	RUNTIME_ERROR = -3
	TIME_LIMIT_EXCEEDED = -2
	WRONG_ANSWER = -1
	ACCEPTED = 1

names = filter(lambda x: x[0]!='_', dir(Result))
numNames = dict([(getattr(Result,i),i.replace('_',' ')) for i in names])

def toString(result):
	if result not in numNames:
		return str(result)
	elif result==Result.INTERNAL_ERROR:
		return 'LOL EI'
	return numNames[result]

def notDone(val):
	return val==Result.PENDING or val==Result.JUDGING

def penaltyTime(val):
	if notDone(val) or val==Result.COMPILE_ERROR:
		return 0
	return 20 if val<0 else 0
