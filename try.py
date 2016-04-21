import requests 

def mainFunc():
	HEADERS = { "User-Agent": "EECS 349 scraper" }
	resRandom = requests.get(r'http://www.reddit.com/r/askreddit/random.json?limit=3', headers = HEADERS)
	dataRandom = resRandom.json()
	postsRandom = dataRandom
	postRandom = postsRandom[0]
	currentRandom = extract_post_info(postRandom["data"]["children"][0]["data"])


	resHot = requests.get(r'http://www.reddit.com/r/askreddit/hot.json?limit=3', headers = HEADERS)
	dataHot = dict(resHot.json())
	postsHot = dataHot["data"]["children"] 
	postHot = postsHot[0]
	currentHot = extract_post_info(postHot["data"])

def extract_post_info(post):
	title = post["title"]
	print title

mainFunc()
