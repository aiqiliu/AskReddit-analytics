#!/usr/bin/env python
import requests
import re
import datetime
import io_tools
import nltk
from pywsd import disambiguate

# from nltk.corpus import wordnet as wn


HEADERS = { "User-Agent": "EECS 349 scraper" }

def get_posts(subreddit, sort, n):
  '''fetch the top 25 posts from the given subreddit
     returns a list of dictionaries containing info about each post
  '''

  # Perform initial query and store response JSON in a dict
  print "Querying /r/%s..." % (subreddit)
  processed = []

  res = requests.get(r'http://www.reddit.com/r/%s/%s.json?limit=%d' % (subreddit, sort, n), headers = HEADERS)
  data = res.json()
  posts = data["data"]["children"]  # Gets post array from API response object
  
  for post in posts:
    # Need ["data"] to traverse API response
    current = extract_post_info(post["data"])
    current["hot"] = 1 if sort == "hot" else 0
    processed.append(current)
    print "Extracting info for post \"%s\"..." % (current["title"])

  return processed


def filter_batch(ts, posts):
  """filters a list of posts according to a given timestamp"""

  filtered = []
  hot_query_time = datetime.datetime.fromtimestamp(ts)

  for p in posts:
    post_time = p["post_utcTime"]
    tdiff = hot_query_time - post_time  # TODO: need to swap depending on direction of range
    if tdiff.days <= 1:
      filtered.append(p)

  return filtered


def extract_post_info(post):
  '''extracts relevant attributes from a post, represented as a dictionary

    returns another dictionary with processed attributes

    - title (string)
    - title_length (numerical)
    - serious (binary)
    - nsfw (binary)
    - post_time (numerical)
    - time_to_first_comment (numerical)
    - author_gold (binary)
    - author_account_age (numerical)
    - author_link_karma (numerical)
    - author_comment_karma (numerical)
  '''

  info = {}

  ##################################
  # TITLE/FLAIR INFO
  # - title
  # - title_length
  # - serious
  # - nsfw
  # - post_id
  ##################################

  # Remove "serious" or "nsfw" tags from title
  # lol what is regex
  title_re = r'(?: ?[\(\[]serious[\)\]] ?)|([\[|\( ]nsfw(?:$|\)|\]) ?)'
  title = re.sub(title_re,
                 "",
                 post["title"],
                 flags=re.IGNORECASE)

  info["title"] = str(title)
  #length by word count 
  info["title_length"] = len(title.split(" "))

  info["serious"] = 1 if post["link_flair_text"] == "serious replies only" else 0
  info["nsfw"] = 1 if post["over_18"] else 0
  info["post_id"] = post["id"]

  ##################################
  # DATE/TIME INFO
  # - post_time
  # - time_to_first_comment
  # - 10min_comment: num of comments in the first 10 mins
  ##################################
  # print str(datetime.datetime.fromtimestamp(post["created"]))

  info["post_utcTime"] = datetime.datetime.fromtimestamp(post["created_utc"])
  info["post_localTime"] = datetime.datetime.fromtimestamp(post["created"])
  # Retrieve first comment
  # TODO: maybe raise the threshold to like 5 comments?
  comments_url = r'http://www.reddit.com/r/%s/comments/%s.json?sort=old' % (post["subreddit"], post["id"])
  comments_res = requests.get(comments_url, headers = HEADERS)
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
        timeDiff = first_comment_time - post["created_utc"]
      else:
        timeDiff = comments_data[i]["data"]["created_utc"] - post["created_utc"]
      # unix time refers to seconds. 10min = 600s
      if timeDiff > 600:
        #break at the first comment later than 10mins of the post posted time 
        info["10min_comment"] = i
        break

    # All comments are within 10mins of post time
    if i == len(comments_data) - 1:
      info["10min_comment"] = i

    # Parse words into question
    info["question_type"] = question_type_classifier(str(title))


    info["senses"] = [word[1] for word in disambiguate(str(title)) if word[1] is not None]

    #Parse title in senses = 
    # print disambiguate(str(title))
    # print '\n\n\n\n'
    # print [word[1] for word in disambiguate(str(title)) if word[1] is not None]

  ##################################
  # AUTHOR INFO
  # - author_gold
  # - author_account_age
  # - author_link_karma
  # - author_comment_karma
  ##################################

  author_url = r'http://www.reddit.com/user/%s/about.json' % (post["author"])
  author_res = requests.get(author_url, headers = HEADERS)
  try:
    author_data = author_res.json()["data"]
    info["author_gold"] = 1 if author_data["is_gold"] else 0
    info["author_link_karma"] = author_data["link_karma"]
    info["author_comment_karma"] = author_data["comment_karma"]
    info["author_account_age"] = info["post_utcTime"] - datetime.datetime.fromtimestamp(author_data["created_utc"])
  except KeyError:
    print "WARNING: author account deleted"
    info["author_gold"] = None
    info["author_link_karma"] = None
    info["author_comment_karma"] = None
    info["author_account_age"] = None

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

  
if __name__ == "__main__":
  sub = "AskReddit"
  sort_by = "hot"
  number_of_posts = 2

  data = get_posts(sub, sort=sort_by, n=number_of_posts)

  #Run through data and compare senses
  sense_array = []
  # print data
  for d in data:
    print d
    for sense in d['senses']:
      print sense
      sense_array.append(sense)
  for d in data:
    for sense in d['senses']:
      print sense
      for comparison_sense in sense_array:
        similarity = sense.path_similarity(comparison_sense)
        if similarity is not None and similarity > 0.5:
          print similarity, comparison_sense
      
  # io_tools.csv_write(data, sort_by)

  # Print out the data minus question titles
  # io_tools.print_data(data, ignore=["title"])

  # dump = [{"kind": "Listing", "data": {"modhash": "", "children": [{"kind": "t3", "data": {"domain": "self.AskReddit", "banned_by": None, "media_embed": {}, "subreddit": "AskReddit", "selftext_html": None, "selftext": "", "likes": None, "suggested_sort": None, "user_reports": [], "secure_media": None, "link_flair_text": None, "id": "48zjvp", "from_kind": None, "gilded": 0, "archived": False, "clicked": False, "report_reasons": None, "author": "cukatie2983", "media": None, "name": "t3_48zjvp", "score": 3, "approved_by": None, "over_18": False, "hidden": False, "thumbnail": "", "subreddit_id": "t5_2qh1i", "edited": False, "link_flair_css_class": None, "author_flair_css_class": None, "downs": 0, "mod_reports": [], "secure_media_embed": {}, "saved": False, "removal_reason": None, "stickied": False, "from": None, "is_self": True, "from_id": None, "permalink": "/r/AskReddit/comments/48zjvp/whats_your_best_yo_mamma_joke/", "locked": False, "hide_score": False, "created": 1457157611.0, "url": "https://www.reddit.com/r/AskReddit/comments/48zjvp/whats_your_best_yo_mamma_joke/", "author_flair_text": None, "quarantine": False, "title": "What's your best \"yo mamma\" joke?", "created_utc": 1457128811.0, "ups": 3, "upvote_ratio": 0.8, "num_comments": 12, "visited": False, "num_reports": None, "distinguished": None}}], "after": None, "before": None}}, {"kind": "Listing", "data": {"modhash": "", "children": [{"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nv8u9", "gilded": 0, "archived": False, "report_reasons": None, "author": "GottIstTot", "parent_id": "t3_48zjvp", "score": 1, "approved_by": None, "controversiality": 0, "body": "Yo Momma so fat she puts mayonnaise on her aspirin!", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo Momma so fat she puts mayonnaise on her aspirin!&lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nv8u9", "score_hidden": False, "stickied": False, "created": 1457157666.0, "author_flair_text": None, "created_utc": 1457128866.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 1}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nvbir", "gilded": 0, "archived": False, "report_reasons": None, "author": "PoppyOncrack", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "You mama is so ugly she made One Direction go the other direction!", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;You mama is so ugly she made One Direction go the other direction!&lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nvbir", "score_hidden": False, "stickied": False, "created": 1457157780.0, "author_flair_text": None, "created_utc": 1457128980.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nvefo", "gilded": 0, "archived": False, "report_reasons": None, "author": "griffen55", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "Yo momma so dumb, when the Genestealers showed up she hid her Levi's...", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo momma so dumb, when the Genestealers showed up she hid her Levi&amp;#39;s...&lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nvefo", "score_hidden": False, "stickied": False, "created": 1457157903.0, "author_flair_text": None, "created_utc": 1457129103.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nvfdk", "gilded": 0, "archived": False, "report_reasons": None, "author": "jesustapdancerchrist", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "Yo mama so fat, she bleeds gravy.", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo mama so fat, she bleeds gravy.&lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nvfdk", "score_hidden": False, "stickied": False, "created": 1457157944.0, "author_flair_text": None, "created_utc": 1457129144.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nvmrc", "gilded": 0, "archived": False, "report_reasons": None, "author": "donriona", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "What's the difference between yo mama and a killer whale? About ten pounds.", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;What&amp;#39;s the difference between yo mama and a killer whale? About ten pounds.&lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nvmrc", "score_hidden": False, "stickied": False, "created": 1457158260.0, "author_flair_text": None, "created_utc": 1457129460.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nvpno", "gilded": 0, "archived": False, "report_reasons": None, "author": "supersmartypants", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "Yo mamma so fat, the earth revolves around her.", "edited": 1457130057.0, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo mamma so fat, the earth revolves around her.&lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nvpno", "score_hidden": False, "stickied": False, "created": 1457158390.0, "author_flair_text": None, "created_utc": 1457129590.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nvste", "gilded": 0, "archived": False, "report_reasons": None, "author": "PM_YOUR_BOOBIES_", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "Yo mama so fat, she's a reddit admin. ", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo mama so fat, she&amp;#39;s a reddit admin. &lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nvste", "score_hidden": False, "stickied": False, "created": 1457158530.0, "author_flair_text": None, "created_utc": 1457129730.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nvtho", "gilded": 0, "archived": False, "report_reasons": None, "author": "PM_YOUR_BOOBIES_", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "Yo mama so ugly, her portraits hang themselves. ", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo mama so ugly, her portraits hang themselves. &lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nvtho", "score_hidden": False, "stickied": False, "created": 1457158558.0, "author_flair_text": None, "created_utc": 1457129758.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nw3n8", "gilded": 0, "archived": False, "report_reasons": None, "author": "mrsuns10", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "Yo mama is so poor that she went to KFC and lick the gravy out of everyone's shoes ", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo mama is so poor that she went to KFC and lick the gravy out of everyone&amp;#39;s shoes &lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nw3n8", "score_hidden": False, "stickied": False, "created": 1457159002.0, "author_flair_text": None, "created_utc": 1457130202.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nx8ch", "gilded": 0, "archived": False, "report_reasons": None, "author": "foureyedsith", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "Yo momma so ugly her picture hang itself. ", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo momma so ugly her picture hang itself. &lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nx8ch", "score_hidden": False, "stickied": False, "created": 1457160754.0, "author_flair_text": None, "created_utc": 1457131954.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0nzcp0", "gilded": 0, "archived": False, "report_reasons": None, "author": "new_skool_hepcat", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "Yo momas so fat that when she got off the plane in Japan, all the Japanese yelled \"it's godzilla!!!\"", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo momas so fat that when she got off the plane in Japan, all the Japanese yelled &amp;quot;it&amp;#39;s godzilla!!!&amp;quot;&lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0nzcp0", "score_hidden": False, "stickied": False, "created": 1457164271.0, "author_flair_text": None, "created_utc": 1457135471.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}, {"kind": "t1", "data": {"subreddit_id": "t5_2qh1i", "banned_by": None, "removal_reason": None, "link_id": "t3_48zjvp", "likes": None, "replies": "", "user_reports": [], "saved": False, "id": "d0o0wj9", "gilded": 0, "archived": False, "report_reasons": None, "author": "Mikeman124", "parent_id": "t3_48zjvp", "score": 0, "approved_by": None, "controversiality": 0, "body": "Yo mama jokes are repulsive, insulting, rude, racist, annoying, overused, frustrating, repetitive, tiring, obnoxious, disgusting, horrid, nonsensical, ugly, bigoted, homophobic, offensive, misogynistic and downright stupid\n\nJust like yo mama! ", "edited": False, "author_flair_css_class": None, "downs": 0, "body_html": "&lt;div class=\"md\"&gt;&lt;p&gt;Yo mama jokes are repulsive, insulting, rude, racist, annoying, overused, frustrating, repetitive, tiring, obnoxious, disgusting, horrid, nonsensical, ugly, bigoted, homophobic, offensive, misogynistic and downright stupid&lt;/p&gt;\n\n&lt;p&gt;Just like yo mama! &lt;/p&gt;\n&lt;/div&gt;", "subreddit": "AskReddit", "name": "t1_d0o0wj9", "score_hidden": False, "stickied": False, "created": 1457166993.0, "author_flair_text": None, "created_utc": 1457138193.0, "distinguished": None, "mod_reports": [], "num_reports": None, "ups": 0}}], "after": None, "before": None}}]

  # current = extract_post_info(dump[0]["data"]["children"][0]["data"])
  # current["hot"] = 0
  # print current