#!/usr/bin/env python

import requests
import re
import datetime
import io_tools

HEADERS = { "User-Agent": "EECS 349 scraper" }

def get_posts(subreddit, sort="hot", n=25):
  '''fetch the top 25 posts from the given subreddit
     returns a list of dictionaries containing info about each post
  '''

  # Perform initial query and store response JSON in a dict
  print "Querying /r/%s..." % (subreddit)
  res = requests.get(r'http://www.reddit.com/r/%s/%s.json?limit=%d' % (subreddit, sort, n), headers = HEADERS)
  data = dict(res.json())
  posts = data["data"]["children"]  # Gets post array from API response object

  processed = []

  for post in posts[1:]:
    print "Extracting info for post \"%s\"..." % (post["data"]["title"])
    # Need ["data"] to traverse API response
    current = extract_post_info(post["data"])
    # Set categorical according to filter mode of query
    current["hot"] = 1 if sort == "hot" else 0
    processed.append(current)

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
  ##################################

  # Remove "serious" or "nsfw" tags from title
  # lol what is regex
  title_re = r'(?: ?[\(\[]serious[\)\]] ?)|([\[|\( ]nsfw(?:$|\)|\]) ?)'
  title = re.sub(title_re,
                 "",
                 post["title"],
                 flags=re.IGNORECASE)

  info["title"] = title
  info["title_length"] = len(title)

  info["serious"] = int(post["link_flair_text"] == "serious replies only")
  info["nsfw"] = int(post["over_18"])

  ##################################
  # DATE/TIME INFO
  # - post_time
  # - time_to_first_comment
  ##################################
  # print str(datetime.datetime.fromtimestamp(post["created"]))

  info["post_time"] = datetime.datetime.fromtimestamp(post["created_utc"])

  # Retrieve first comment
  # TODO: maybe raise the threshold to like 5 comments?
  comments_url = r'http://www.reddit.com/r/%s/comments/%s.json?sort=old&limit=1' % (post["subreddit"], post["id"])
  comments_res = requests.get(comments_url, headers = HEADERS)
  comments_data = comments_res.json()[1]["data"]["children"]

  if len(comments_data) is 0:
    # If the post has no comments, set value to 0
    info["time_to_first_comment"] = 0
  else:
    if "created_utc" in comments_data[0]["data"].keys():
      comment_time = comments_data[0]["data"]["created_utc"]
    else:
      # Catch a weird case when the oldest comment doesn't have the "created_utc" field
      oldest_comment_id = comments_data[0]["data"]["id"]
      oldest_comment_res = requests.get(r'http://www.reddit.com/r/%s/comments/%s.json?comment=%s' % (post["subreddit"], post["id"], oldest_comment_id), headers = HEADERS)
      comment_time = oldest_comment_res.json()[1]["data"]["children"][0]["data"]["created_utc"]

    # Compute timedelt from post creation to comment creation
    comment_datetime = datetime.datetime.fromtimestamp(comment_time)
    info["time_to_first_comment"] = comment_datetime - info["post_time"]

  ##################################
  # AUTHOR INFO
  # - author_gold
  # - author_account_age
  # - author_link_karma
  # - author_comment_karma
  ##################################

  author_url = r'http://www.reddit.com/user/%s/about.json' % (post["author"])
  author_res = requests.get(author_url, headers = HEADERS)

  if "data" in author_res.json().keys():
    author_data = author_res.json()["data"]

    info["author_gold"] = int(author_data["is_gold"])
    info["author_link_karma"] = author_data["link_karma"]
    info["author_comment_karma"] = author_data["comment_karma"]
    info["author_account_age"] = info["post_time"] - datetime.datetime.fromtimestamp(author_data["created_utc"])
  else:
    # Catch the case where the user deleted their account
    print "\tWARNING: No author information available"
    author_attrs = ["author_gold", "author_link_karma", "author_comment_karma", "author_account_age"]
    for a in author_attrs:
        info[a] = None


  return info


if __name__ == "__main__":
  sub = "AskReddit"
  sort_by = "hot"
  number_of_posts = 25

  data = get_posts(sub, sort=sort_by, n=number_of_posts)
  io_tools.csv_write(data)

  # Print out the data minus question titles
  io_tools.print_data(data, ignore=["title"])