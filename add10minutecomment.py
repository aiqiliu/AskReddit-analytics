import requests
import re
import datetime
import io_tools
import csv

HEADERS = { "User-Agent": "EECS 349 scraper" }


def getTimeInfo(row):
	info = {}
	info["post_utcTime"] =  datetime.datetime.strptime(row[11], '%m/%d/%y %H:%M') #convert some data
	comments_url = r'http://www.reddit.com/r/AskReddit/comments/%s.json?sort=old' % (row[5])
	comments_res = requests.get(comments_url, headers = HEADERS)
	post_utcTime = comments_res.json()[0]["data"]["children"][0]["data"]["created_utc"]
	comments_data = comments_res.json()[1]["data"]["children"]

	if len(comments_data) is 0:
	  	# If the post has no comments, set value to 0
	  	# get number of total comments
		info["time_to_first_comment"] = 0
		info["10min_comment"] = 0
	else:
		if "created_utc" in comments_data[0]["data"].keys():
			first_comment_time = comments_data[0]["data"]["created_utc"]
		else:
			# Catch a weird case when the oldest comment doesn't have the "created_utc" field
			oldest_comment_id = comments_data[0]["data"]["id"]
			oldest_comment_res = requests.get(r'http://www.reddit.com/r/%s/comments/%s.json?comment=%s' % (post["subreddit"], post["id"], oldest_comment_id), headers = HEADERS)
			first_comment_time = oldest_comment_res.json()[1]["data"]["children"][0]["data"]["created_utc"]

		first_comment_datetime = datetime.datetime.fromtimestamp(first_comment_time)
		info["time_to_first_comment"] = first_comment_datetime - info["post_utcTime"]


		for i in range(0, len(comments_data)):
			if i == 0: #correspond of previous case when oldest comment doesn't have "created_utc"
				timeDiff = first_comment_time - post_utcTime
			else:
				timeDiff = comments_data[i]["data"]["created_utc"] - post_utcTime
			# unix time refers to seconds. 10min = 600s
			if timeDiff > 600:
				#break at the first comment later than 10mins of the post posted time
				info["10min_comment"] = i
				break

		# All comments are within 10mins of post time
		if i == len(comments_data) - 1:
			info["10min_comment"] = i
	return info

def getAuthorData(row):
	info = {}
	comments_url = r'http://www.reddit.com/r/AskReddit/comments/%s.json?sort=old' % (row[5])
	comments_res = requests.get(comments_url, headers = HEADERS)
	author = comments_res.json()[0]["data"]["children"][0]["data"]["author"]

	author_url = r'http://www.reddit.com/user/%s/about.json' % (author)
	author_res = requests.get(author_url, headers = HEADERS)
	try:
	  author_data = author_res.json()["data"]
	  info["author_gold"] = 1 if author_data["is_gold"] else 0
	  
	except KeyError:
	  print "WARNING: author account deleted"
	  info["author_gold"] = None

	return info

def question_type_classifier(title):
	##################################
	# QUESTION TYPE
	# 1 -> Who
	# 2 -> Where
	# 3 -> When
	# 4 -> Why
	# 5 -> What
	# 6 -> Which
	# 7 -> How
	# 0 -> Could not find
	##################################
	question_types = [
		'', #Blank for could not find
		'who',
		'where',
		'when',
		'why',
		'what',
		'which',
		'how'
	]
	# Convert words in title to lowercase and then split by spaces
	title_array = title.lower().split()

	for word in title_array:
		for i in range(1, len(question_types)):
			if word.find(question_types[i]) >= 0:
				return i
	return 0





def addMissingInfo(fileList):
	#Order in which the old headers are written in the csv
	# get titles from csv
	print 'here'
	for filename in fileList:
		print "Reading " + filename + ".csv and..."
		print "Writing " + filename + "_fixed.csv..."
		with open(filename + '.csv', 'rU') as csvfile_read:	#Read CSV
			with open(filename + '_fixed.csv', 'wb') as csvfile_write:
				reader = csv.reader(csvfile_read)
				writer = csv.writer(csvfile_write)
				writer.writerow(next(reader)) # Write header
				for row in reader:
					

					# Time Info
					print getTimeInfo(row)
					print getAuthorData(row)



					
					exit()
					#End of add 10 minute comment
					
					writer.writerow(row)
					print scores


if __name__ == "__main__":
	fileList = ['./DATA/devDataMay31toJun3']
	addMissingInfo(fileList)


