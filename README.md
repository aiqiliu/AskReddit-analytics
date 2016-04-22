# AskReddit Analytics

Predicting the performance of [/r/AskReddit](http://reddit.com/r/askreddit) submissions.

EECS 349 project by:

* [Sarah Lim](http://github.com/sarahlim)
* [Aiqi Liu](http://github.com/aiqiliu)
* [Jennie Werner](http://github.com/jenniewerner)
* [Sameer Srivastava](http://github.com/sameersrivastava)

## Getting started

With Python installed, you can pull a new batch of data by executing `query.py` from the terminal:

```
./query.py
```

`query.py` allows you to specify a subreddit, a sortview, and a number of posts, fetches information about the corresponding posts, and writes the output to a timestamped CSV file.

By default, `query.py` executes the following parameters:

* **Subreddit:** `"AskReddit"`
* **Sort view:** `"hot"`
* **Number of posts:** `25`

CSV files are saved to the `/hot` and  `/random` directory.

### Attributes

`query.py` returns the following attributes:

* title (string)
* title_length (numerical)
* serious (binary)
* nsfw (binary)
* post_time (numerical)
* time_to_first_comment (numerical)
* author_gold (binary)
* author_account_age (numerical)
* author_link_karma (numerical)
* author_comment_karma (numerical)

## TODO

* [ ] Make sure it works for "non-hot" data  
* [ ] Implement duplicate detection and removal for posts...honestly, figure out what to do with duplicates to begin with lol  
* [ ] Set up as a cron job on raspberry pi  
