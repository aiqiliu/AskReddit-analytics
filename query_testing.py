import requests
import json
import datetime

def get_posts(subreddit, sort="hot", n=25):
  '''fetch the top 25 posts from the given subreddit

     return a list of dictionaries containing info about each post
  '''

  # Perform initial query and store response JSON in a dict
  print "Querying /r/%s..." % (subreddit)
  res = requests.get(r'http://www.reddit.com/r/%s/%s.json?limit=%d' % (subreddit, sort, n), headers = headers)
  data = dict(res.json())
  posts = data["data"]["children"]  # Gets post array from API response object

  processed = []

  for post in posts[1:]:
    current = extract_post_info(post["data"])  # Need ["data"] to traverse API response

    # Set categorical according to filter mode of query
    current["hot"] = 1 if sort == "hot" else 0

    processed.append(current)

  return processed


def extract_post_info(post):
  '''extracts relevant attributes from a post, represented as a dictionary

    returns another dictionary with processed attributes

    POST INFO:
    - String title
    - Number title_length
    - Bool serious
    - Number utc_post_time
    - Number time_to_first_comment http://reddit.com/r/AskReddit/comments/4fgtt7.json

    AUTHOR INFO:
    - Bool author_gold
    - Number author_account_age /user/USERNAME/about.json[created-utc]
    - Number author_link_karma
    - Number author_comment_karma
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
  title = re.sub(r'(?: ?[\(\[]serious[\)\]] ?)|([\[|\( ]nsfw(?:$|\)|\]) ?)',
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
  comments_res = requests.get(r'http://www.reddit.com/r/%s/comments/%s.json?sort=old&limit=1' % (str(post["subreddit"]), str(post["id"])), headers = headers)
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

  author_res = requests.get(r'http://www.reddit.com/user/%s/about.json' % (post["author"]), headers = headers)
  author_data = author_res.json()["data"]

  info["author_gold"] = 1 if author_data["is_gold"] else 0
  info["author_link_karma"] = author_data["link_karma"]
  info["author_comment_karma"] = author_data["comment_karma"]
  info["author_account_age"] = info["post_time"] - datetime.datetime.fromtimestamp(author_data["created_utc"])

  return info


if __name__ == "__main__":
  headers = { 'User-Agent': "EECS 349 scraper" }
  subreddit = "AskReddit"
  print get_posts(subreddit, n=3)
