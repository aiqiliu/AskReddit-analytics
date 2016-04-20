import praw

r = praw.Reddit(user_agent='askRedditTop')
submissions = r.get_subreddit('askreddit').get_hot(limit=5)
print submissions