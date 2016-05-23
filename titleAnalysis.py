# Finished: 
# training for purely tokens of the titles
# probability of a sense/token belongs to the hot set

# In Progress:
# Find a way to hash the Synset for train_senses_set. 
# Problem: key Synset('teacher.n.02') is not hashable
# Fix: 1. Use two parallel lists, one for all the Synsets and one for corresponding num of occurences
#      2. Create some sort of Synset object (not sure if it works)

# TO DO:
# Fix senses classifier to use total again (May not matter, but would be nice to have number between 0 and 1)

import nltk, math
nltk.download('punkt')
from nltk.corpus import wordnet as wn
import csv, os, pickle
from nltk.corpus import stopwords
from nltk import pos_tag, word_tokenize
from pywsd import disambiguate
from math import log
import matplotlib.pyplot as plt


global hot_senses_dict, hot_token_dict, hot_token_total
hot_senses_dict = {}
hot_token_dict = {}
hot_token_total = 0
stop = stopwords.words('english')

def train_senses_set(title):
	global hot_senses_dict
	# extract the words that are not none with their synset
	senses = [word[1].name() for word in disambiguate(str(title)) if word[1] is not None]
	for sense in senses:
		if sense in hot_senses_dict:
			hot_senses_dict[sense] += 1
		else:
			hot_senses_dict[sense] = 1
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

def classify(text, category, dictionary, total = 0): #category = "senses" or "token"
    # seprate the text into tokens 
    if category == "sense":
    	tokens = [word[1].name() for word in disambiguate(text) if word[1] is not None]
    else:
    	tokens = word_tokenize(text)
    	tokens = [word for word in tokens if word not in stop]
    	tokens = filter(lambda word: word not in [',', '.', '!', '?', '``', "'ve", "''", "n't", "'s"], tokens)
    return probability(tokens, category, dictionary, total)

def probability(tokens, category, dictionary, total):   	  
	if category == "sense":
		total_score = 0
		dic = dictionary
		if len(tokens) == 0:
			return 0
		for token in tokens:
			for dict_sense in dic:
				score = wn.synset(token).path_similarity(wn.synset(dict_sense))
				if score is not None:
					total_score += score * dic[dict_sense]
		return (total_score/len(tokens))
	else:
		p = 0 
		dic = dictionary
		total_instances = total
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
	global hot_senses_dict, hot_token_dict, hot_token_total
	# train_set("teacher")
	# print hot_senses_dict == {Synset('teacher.n.02'): 1}
	
	train_senses_set("teacher")
	train_senses_set("teacher")
	print hot_senses_dict == {u'teacher.n.02': 2} 
	print train_token_set("beautiful world") == {'world': 1, 'beautiful': 1}
	print train_token_set("I am beautiful") == {'world': 1, 'beautiful': 2 , 'I': 1}
	print classify("China", "token", hot_token_dict, hot_token_total) == 0
	print classify("I","token", hot_token_dict, hot_token_total) == 0.25
	print classify("beautiful","token", hot_token_dict, hot_token_total) == 0.5
	print classify("teacher","sense", hot_senses_dict) == 2.0

	# print hot_senses_dict
	# print hot_token_dict

	#clear dictionaries
	hot_senses_dict = {}
	hot_token_dict = {}

def training():
	#Manually list out files in DATA folder
	fileList = ['devDataMay1to4.csv','devDataMay16to18.csv']
	titles = []
	# get titles from csv
	for filename in fileList:
		print "Reading " + filename + "..."
		with open('./DATA/' + filename, 'rU') as csvfile:			
			reader = csv.reader(csvfile)
			next(reader) # Ignore first row

			for row in reader:
				titles.append(row[5])
				print row[5]
	# print titles


if __name__ == "__main__":
	unit_tests()
	training()
	exit()
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
	# for title in titles:
	# 	print title
	# 	train_senses_set(title)
	# 	train_token_set(title)

	# print "Writing to cache..."
	# # save the dict into cache
	# f = open('cache.p', "w")
	# p = pickle.Pickler(f)
	# p.dump([hot_senses_dict, hot_token_dict, hot_token_total])
	# f.close()
	# print "training set saved into cache.p"

	# Check if you can read dictionaries
	cached_hot_senses_dict, cached_hot_token_dict, cached_hot_token_total = pickle.load(open("cache.p", "rb"))

	print "Classify..."
	sense_scores = []
	token_scores = []
	for title in titles:
		print title
		sense_scores.append(classify(title,"sense",cached_hot_senses_dict))
		token_scores.append(classify(title,"token",cached_hot_token_dict, cached_hot_token_total))

	
	plt.hist(sense_scores, 50, normed=1, facecolor='red', alpha=0.75)

	plt.grid(True)
	plt.show()

	plt.hist(token_scores, 50, normed=1, facecolor='green', alpha=0.75)
	plt.grid(True)
	plt.show()


		
	



















