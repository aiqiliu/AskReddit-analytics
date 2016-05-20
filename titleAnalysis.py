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
from nltk.corpus import wordnet as wn
import csv, os, pickle
from nltk.corpus import stopwords
from nltk import pos_tag, word_tokenize
from pywsd import disambiguate
from math import log

global hot_senses_dict, hot_token_dict, hot_senses_total, hot_token_total
hot_senses_dict = {}
hot_token_dict = {}
hot_senses_total = hot_token_total = 0
stop = stopwords.words('english')

def train_senses_set(title):
	global hot_senses_dict, hot_senses_total
	# extract the words that are not none with their synset
	senses = [word[1].name() for word in disambiguate(str(title)) if word[1] is not None]
	for sense in senses:
		if sense in hot_senses_dict:
			hot_senses_dict[sense] += 1
		else:
			hot_senses_dict[sense] = 1
		hot_senses_total += 1
	return hot_senses_dict

def train_token_set(title):
	global hot_token_dict, hot_token_total
	# only keep the useful words
	tokens = word_tokenize(title)
	tokens = [word for word in tokens if word not in stop]
	tokens = filter(lambda word: word not in [',', '.', '!', '?', '``', "'ve", "''", "n't", "'s"], tokens)
	for token in tokens:
		if token in hot_token_dict:
			hot_token_dict[token] += 1
		else:
			hot_token_dict[token] = 1
		hot_token_total += 1
	return hot_token_dict

def classify(text, category): #category = "senses" or "token"
    # seprate the text into tokens 
    if category == "sense":
    	tokens = [word[1].name() for word in disambiguate(text) if word[1] is not None]
    else:
    	tokens = word_tokenize(text)
    	tokens = [word for word in tokens if word not in stop]
    	tokens = filter(lambda word: word not in [',', '.', '!', '?', '``', "'ve", "''", "n't", "'s"], tokens)
    return probability(tokens, category)

def probability(tokens, category):   	  
	if category == "sense":
		total_score = 0
		dic = hot_senses_dict
		total_instances = hot_senses_total
		for token in tokens:
			for dict_sense in hot_senses_dict:
				score = wn.synset(token).path_similarity(wn.synset(dict_sense))
				if score is not None:
					total_score += score * hot_senses_dict[dict_sense]
		return total_score
	else:
		p = 0 
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


def unit_tests():
	print "Running Unit Tests..."
	global hot_senses_dict, hot_token_dict
	# train_set("teacher")
	# print hot_senses_dict == {Synset('teacher.n.02'): 1}
	
	train_senses_set("teacher")
	train_senses_set("teacher")
	print hot_senses_dict == {u'teacher.n.02': 2} 
	print train_token_set("beautiful world") == {'world': 1, 'beautiful': 1}
	print train_token_set("I am beautiful") == {'world': 1, 'beautiful': 2 , 'I': 1}
	print classify("China", "token") == 0
	print classify("I","token") == 0.25
	print classify("beautiful","token") == 0.5
	print classify("teacher","sense") == 2.0

	print hot_senses_dict
	print hot_token_dict

	#clear dictionaries
	hot_senses_dict = {}
	hot_token_dict = {}

if __name__ == "__main__":
	unit_tests()
	# exit()
	# a list of the csv file names 
	fileList = []
	for fFileObj in os.walk("./hot"): 
		fileList = fFileObj[2]
		break

	fileList = fileList[1:] # get rid of the '.Dstore'
	titles = []
	# get titles from csv
	for filename in fileList:
		print "Reading " + filename + "..."
		with open('./hot/' + filename, 'rb') as csvfile:			
			reader = csv.reader(csvfile)
			next(reader) # Ignore first row

			for row in reader:
				titles.append(row[5])
	print "Training dataset..."
	# train the tokens
	i = 0
	for title in titles:
		print title
		train_token_set(title)
		train_senses_set(title)
		i += 1
		if i > 25:
			break

	print hot_senses_dict
	print hot_token_dict

	# print "Writing to cache..."
	# # save the dict into cache
	# f = open('cache.p', "w")
	# p = pickle.Pickler(f)
	# p.dump([hot_senses_dict, hot_token_dict])
	# f.close()
	# print "training set saved into cache.p"

	#Check if you can read dictionaries
	# cached_hot_senses_dict, cached_hot_token_dict = pickle.load(open("cache.p", "rb"))
	# print cached_hot_token_dict == hot_token_dict
	# print cached_hot_senses_dict == hot_senses_dict

	print "Classify..."
	i = 0
	for title in titles:
		print title
		print "token score: " + str(classify(title,"token"))
		print "sense score: " + str(classify(title,"sense"))
		i += 1
		if i > 25:
			break
	



















