import requests
import re
import datetime
import io_tools

def get_posts(subreddit, sort="hot", n=25):
  '''fetch the top 25 posts from the given subreddit
     returns a list of dictionaries containing info about each post
  '''

  # Perform initial query and store response JSON in a dict
  print "Querying /r/%s..." % (subreddit)
  res = requests.get(r'http://www.reddit.com/r/%s/%s.json?limit=%d' % (subreddit, sort, n), headers = headers)
  data = dict(res.json())
  posts = data["data"]["children"]  # Gets post array from API response object

  processed = []

  for post in posts[1:]:
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

  info["title"] = str(title)
  info["title_length"] = len(title)

  info["serious"] = 1 if post["link_flair_text"] == "serious replies only" else 0
  info["nsfw"] = 1 if post["over_18"] else 0

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
  comments_res = requests.get(comments_url, headers = headers)
  comments_data = comments_res.json()[1]["data"]["children"]

  if len(comments_data) is 0:
    # If the post has no comments, set value to 0
    info["time_to_first_comment"] = 0
  else:
    # Compute timedelt from post creation to comment creation
    comment_time = comments_data[0]["data"]["created_utc"]
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
  author_res = requests.get(author_url, headers = headers)
  author_data = author_res.json()["data"]

  info["author_gold"] = 1 if author_data["is_gold"] else 0
  info["author_link_karma"] = author_data["link_karma"]
  info["author_comment_karma"] = author_data["comment_karma"]
  info["author_account_age"] = info["post_time"] - datetime.datetime.fromtimestamp(author_data["created_utc"])

  return info


if __name__ == "__main__":
  headers = { 'User-Agent': "EECS 349 scraper" }
  subreddit = "AskReddit"
  data = get_posts(subreddit, n=3)
  print data
  io_tools.csv_write(data)
  io_tools.print_data(data, ignore=["title"])