import json
import glob
from hotQuery import extract_post_info
from io_tools import csv_write

processed = []
folderName = "conv5"

def loadFile(fileName):
    myFile = open(fileName)
    fileData = myFile.read()
    data = json.loads(fileData)
    post = data[0]["data"]["children"]
    return post


def run():
    jsonFileNames = glob.glob(folderName +"/*.json")
    for fileName in jsonFileNames:
        print fileName
        post = loadFile(fileName)
        current = extract_post_info(post[0]["data"])
        current["hot"] = 0
        processed.append(current)
        #print "Extracting info for post \"%s\"..." % (current["title"])

    return processed

formattedData = run()
csv_write(formattedData, "scrapedRandom")
