import requests
import re
res = requests.get('https://www.reddit.com/r/AskReddit/comments/4m1v8q/who_is_currently_on_the_wrong_side_of_history')
data = dict(res.json())
print data