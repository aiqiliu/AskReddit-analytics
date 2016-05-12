# get the date as a string. return a datetime object 
# hot_May.03_23.09PM.csv
import datetime
def getComponent(s):
	print s
	firstDot = s.find('.')
	firstUnderline = s.find('_')
	month = s[firstUnderline + 1: firstDot]
	months = {'May': 5, 'Jun': 6}
	month = months[month]
	print month
	s = s[firstDot + 1:]
	firstUnderline = s.find('_')
	day = s[:firstUnderline]
	print day
	s = s[firstUnderline + 1:]
	firstDot = s.find('.')
	hour = s[:firstDot]
	print hour
	s = s[firstDot + 1:]
	minute = s[:2]
	print minute
	convertToUtc(month, int(day), int(hour), int(minute))

def convertToUtc(month, day, hour, minute):
	utc = datetime.datetime(2016, month, day, hour, minute)
	print utc
	return utc

