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
	synset = [word[1].name() for word in disambiguate(str(title)) if word[1] is not None]
	for instance in synset:
		found = 0
		if len(hot_senses_dict) != 0:
			for sense in hot_senses_dict:
				# loop throught exisiting senses in the dict
				# compare token with current senses
				similarity = wn.synset(sense).path_similarity(wn.synset(instance))
				if similarity is not None and similarity > 0.5:
					hot_senses_dict[sense] += 1
					found = 1
					break
		# create new sense if no similar senses 
		if found == 0:
			hot_senses_dict[instance] = 1
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
    if category == "senses":
    	tokens = [word[1].name() for word in disambiguate(text) if word[1] is not None]
    else:
    	tokens = word_tokenize(text)
    	tokens = [word for word in tokens if word not in stop]
    	tokens = filter(lambda word: word not in [',', '.', '!', '?', '``', "'ve", "''", "n't", "'s"], tokens)
    return probability(tokens, category)

def probability(tokens, category):
	p = 0    	  
	if category == "senses":
		dic = hot_senses_dict
		total_instances = hot_senses_total
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
	print classify("teacher","senses") == 1.0

	#clear dictionaries
	hot_senses_dict = {}
	hot_token_dict = {}

if __name__ == "__main__":
	unit_tests()
	print hot_senses_dict
	print hot_token_dict
	exit()
	# a list of the csv file names 
	fileList = []
	for fFileObj in os.walk("./hot"): 
		fileList = fFileObj[2]
		break

	fileList = fileList[1:] # get rid of the '.Dstore'
	titles = []
	# get titles from csv
	for filename in fileList:
		with open('./hot/' + filename, 'rb') as csvfile:			
			reader = csv.reader(csvfile)
			next(reader) # Ignore first row

			for row in reader:
				titles.append(row[5])
	# train the tokens
	for title in titles:
		train_token_set(title)
	# save the dict into cache
	f = open('cache.txt', "w")
	p = pickle.Pickler(f)
	p.dump([hot_senses_dict, hot_token_dict])
	f.close()
	print "training set saved into cache.txt"


















