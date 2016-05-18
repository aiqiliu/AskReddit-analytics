# Finished: 
# training for purely tokens of the titles
# probability of a sense/token belongs to the hot set

# In Progress:
# Find a way to hash the Synset for train_senses_set. 
# Problem: key Synset('teacher.n.02') is not hashable
# Fix: 1. Use two parallel lists, one for all the Synsets and one for corresponding num of occurences
#      2. Create some sort of Synset object (not sure if it works)

# TO DO:
# write function to read titles from csv
# train the actual data sets 
# save the cache of the training info so that the classification can just load the dicts

import nltk, math
nltk.download('punkt')
from nltk import pos_tag, word_tokenize
from pywsd import disambiguate
from math import log

global hot_senses_dict, hot_token_dict, hot_sensens_total, hot_token_total
hot_senses_dict = hot_token_dict = {}
hot_sensens_total = hot_token_total = 0

def train_senses_set(title):
	global hot_senses_dict, hot_sensens_total
	# extract the words that are not none with their synset
	synset = [word[1] for word in disambiguate(str(title)) if word[1] is not None]
	for instance in synset:
		found = 0
		if len(hot_senses_dict) != 0:
			for sense in hot_senses_dict:
				# loop throught exisiting senses in the dict
				# compare token with current senses
				similarity = sense.path_similarity(instance)
				if similarity is not None and similarity > 0.5:
					hot_senses_dict[sense] += 1
					found = 1
					break
		# create new sense if no similar senses 
		if found == 0:
			hot_senses_dict[instance] = 1
		hot_sensens_total += 1
	return hot_senses_dict

def train_token_set(title):
	global hot_token_dict, hot_token_total
	# only keep the words
	synset = [word[0] for word in disambiguate(str(title)) if word[1] is not None]
	for token in synset:
		if token in hot_token_dict:
			hot_token_dict[token] += 1
		else:
			hot_token_dict[token] = 1
		hot_token_total += 1
	return hot_token_dict

def classify(text, category): #category = "senses" or "token"
    # seprate the text into tokens 
    tokens = [word[0] for word in disambiguate(text) if word[1] is not None]
    return probability(tokens, category)

def probability(tokens, category):
	p = 0    	  
	if category == "senses":
		dic = hot_senses_dict
		total_instances = hot_sensens_total
	else:
		dic = hot_token_dict
		total_instances = hot_token_total
	  
	for token in tokens:
	    if token in dic:
	    	token_prob = dic[token]
	    else:
	    	token_prob = 0
	    # smooth one out
	    curr = token_prob/float(total_instances)
	    p += curr 

	return p


def test():
	# train_set("teacher")
	# print hot_senses_dict == {Synset('teacher.n.02'): 1}
	
	# train_set("teacher")
	# print hot_senses_dict == {Synset('teacher.n.02'): 2} 
	print train_token_set("beautiful world") == {'world': 1, 'beautiful': 1}
	print train_token_set("I am beautiful") == {'world': 1, 'beautiful': 2}
	print classify("China", "token") == 0
if __name__ == "__main__":
	test()
	titles = ["Announcing our contest winner and some other stuff", "Redditors with great parents, What did they do RIGHT?"]
	for title in titles:
		train_token_set(title)
		# train_senses_set(title)
	print classify("winner is cool", "token")
	# print classify("winner is cool", "senses")






