import requests
import json
import re
import os
import time
from datetime import datetime

headers = {
            'User-Agent': "EECS 349 scraper"
          }

unneededFields = ["subreddit_id", "banned_by", "subreddit", "saved", "id", "parent_id", "approved_by", "edited", "author_flair_css_class", "body_html", "link_id", "score_hidden", "name", "created", "author_flair_text", "distinguished", "num_reports"]

reddits = ["askreddit"]

cwd = os.getcwd() #"current working directory"

def removeUnneededFieldsFromData(comment):
    if comment["kind"] == "t1":
        for f in unneededFields:
            if f in comment["data"]:
                del comment["data"][f]
        if "replies" in comment["data"] and len(comment["data"]['replies']) > 0:
            for c in comment["data"]['replies']["data"]["children"]:
                removeUnneededFieldsFromData(c)
    elif comment["kind"] == "more":
        del comment["data"]


def stripAndSave(link):
    starttime = time.time()
    url = r'http://www.reddit.com%s.json' % (link[:-1])
    raw = requests.get(url, headers=headers)
    data = raw.json()
    subreddit = data[0]["data"]["children"][0]["data"]["subreddit"]
    title = data[0]["data"]["children"][0]["data"]["permalink"]
    # Extract the unique part of the Reddit URL, ie the parts after 'comment/'
    m = re.search('comments/([\w\d]+/[\w+]+)', title) 
    title = m.group(1)
    title = re.sub('/', ':', title)
    filename = "r/" + subreddit + "/" + title + ".json"
    for child in data[1]["data"]["children"]:
       removeUnneededFieldsFromData(child) # strip the irrelevant cruft from the json files, halving their storage space
    if not os.path.isdir(cwd + "/" + subreddit):
        try:
            os.makedirs("r/" + subreddit + "/")
        except OSError, e:
            if e.errno != 17: # This error is simply signalling that the directories exist already. Therefore, ignore it
                raise #if it's a different error, "raise" another error
    f = open(filename, "w")
    f.write(json.dumps(data))
    f.close()
    endtime = time.time()
    if endtime - starttime < 2:
        time.sleep(2 - (endtime - starttime))


if __name__ == "__main__"
    # loopstart = time.time()
    for reddit in reddits:
        print "Reading from subreddit /r/%s" % (reddit)
        r = requests.get(r'http://www.reddit.com/r/%s/hot.json?limit=3' % (reddit), headers = headers)
        data = r.json()

        # A list of reddit Thing objects that are posts.
        postedThings = data["data"]["children"]
        counter = 1;
        result = ""
        for thing in postedThings:
            if not thing["data"]["stickied"] == 1: 
                #relevate attr: title, serious flag, time of post
                #length of title(word count)
                #author account age, total author karma
                title = thing["data"]["title"]            
                serious = str('Serious' in title) + ' '
                if serious: #leave the title purely the title itself 
                    title = title.replace("[Serious]","")
                titleLen = str(len(title.split())) + ' '
                #doubt about the time, even if the time is tracked, the time is based on chicago time and reddit has users from everywhere
                utcTime = thing["data"]["created_utc"]
                utcTime = datetime.fromtimestamp(int(utcTime)).strftime('%Y-%m-%d %H:%M') + ' '
                
                localTime = thing["data"]["created"]
                localTime = datetime.fromtimestamp(int(localTime)).strftime('%Y-%m-%d %H:%M') + ' '

                author = thing["data"]["author"]
                authorQuery = requests.get(r'http://www.reddit.com/%s/about.json' % (author), headers = headers)
                linkKarma = 
                #length of children array for that person
                #comments karma, link karma
                result += title + titleLen + serious + utcTime + localTime + '\n'
                counter += 1
                # stripAndSave(thing["data"]["permalink"])
        print result









# TODO: format output with CSV
# get author account age, comment_karma, link_karma
# isGold
# account age: /user/USERNAME/about.json[created-utc]
# ^ need to generate current UTC timestamp
# Time to first comment http://reddit.com/r/AskReddit/comments/4fgtt7.json

- Length of title (numerical)
- Serious flag (boolean)
- Time of post (local)
- Time of post (standard)
- Author account age (date) *
- Author link karma *
- Author comment karma *
- Time to first comment *


