import json
import glob
from hotQuery import extract_post_info
from io_tools import csv_write

processed = []
folderName = "Data/devDataMay16to18"

def loadFile(fileName):
    myFile = open(fileName)
    fileData = myFile.read()
    data = json.loads(fileData)
    post = data[0]["data"]["children"]
    return post


def run(hotPosts):
    jsonFileNames = glob.glob(folderName +"/*.json")

    for fileName in jsonFileNames:
        print fileName[25:31]
        if fileName[25:31] not in hotPosts:
            #print fileName
            post = loadFile(fileName)
            current = extract_post_info(post[0]["data"])
            current["hot"] = 0
            processed.append(current)
        #print "Extracting info for post \"%s\"..." % (current["title"])
        else:
            print "duplicate value"

    return processed



hotPosts = ["4js1kz",
"4jzltd",
"4jw8zs",
"4jj45x",
"4jkhhg",
"4jyiu4",
"4ji642",
"4jwr3t",
"4jzjpo",
"4jrhqv",
"4jqj1a",
"4jy0ku",
"4jpy57",
"4jzouu",
"4jxupe",
"4js3rb",
"4jl7ow",
"4jscq9",
"4jw950",
"4jqdfn",
"4jqfka",
"4jr4sy",
"4jwi0t",
"4jyutx",
"4jjn24",
"4jl47m",
"4jsttj",
"4ju1qm",
"4jkzvm",
"4jwdsw",
"4jrwrr",
"4jkaoe",
"4jifo2",
"4jq761",
"4jzw9f",
"4jjm7v",
"4jqtsm",
"4jsmr5",
"4jwexq",
"4jtyii",
"4jymdh",
"4jkwm9",
"4jibyr",
"4jqszd",
"4jfzij",
"4ji3sm",
"4jl0dr",
"4jvp0x",
"4jsxgf",
"4jkpt6",
"4jjhh6",
"4jimna",
"4jkleh",
"4jwnbz",
"4jtdia",
"4jzxst",
"4jr080",
"4jktha",
"4jhfu4",
"4jw61z",
"4jzti5",
"4jrolp",
"4jqp4r",
"4jw90v",
"4jjibg",
"4jwjtx",
"4jkl5o",
"4ji4yw",
"4jrn67",
"4jyl1e",
"4ju3rx",
"4jz5tr",
"4jsmun",
"4jl4e6",
"4jiyoa"]

formattedData = run(hotPosts)
print formattedData
csv_write(formattedData, "scrapedRandom")
