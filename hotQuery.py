#!/usr/bin/env python
import requests
import re
import datetime
import io_tools

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

  for post in posts[1:]:
    # Need ["data"] to traverse API response
    current = extract_post_info(post["data"])
    current["hot"] = 1 if sort == "hot" else 0
    processed.append(current)
    print "Extracting info for post \"%s\"..." % (current["title"])

  return processed


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

  ##################################
  # AUTHOR INFO
  # - author_gold
  # - author_account_age
  # - author_link_karma
  # - author_comment_karma
  ##################################

  author_url = r'http://www.reddit.com/user/%s/about.json' % (post["author"])
  author_res = requests.get(author_url, headers = HEADERS)
  author_data = author_res.json()["data"]

  info["author_gold"] = 1 if author_data["is_gold"] else 0
  info["author_link_karma"] = author_data["link_karma"]
  info["author_comment_karma"] = author_data["comment_karma"]
  info["author_account_age"] = info["post_utcTime"] - datetime.datetime.fromtimestamp(author_data["created_utc"])

  return info


if __name__ == "__main__":
  sub = "AskReddit"
  sort_by = "hot"
  number_of_posts = 25

  data = get_posts(sub, sort=sort_by, n=number_of_posts)

  io_tools.csv_write(data, sort_by)

  # Print out the data minus question titles
  io_tools.print_data(data, ignore=["title"])
