import csv
import datetime
import os

def print_data(lst, ignore=[]):
  '''nicely print a list of dictionaries in tabular format'''

  # Most attribute values will be the same length, so we only
  # check the first entry as a heuristic
  max_length = max([len(str(val)) for key, val in lst[0].iteritems() if key not in ignore]) + 2

  # Print header row
  header_row = ''.join([key.upper().ljust(max_length) for key in lst[0].keys() if key not in ignore])
  print header_row

  # Print each row in a column
  for entry in lst:
    print ''.join([str(val).ljust(max_length) for key, val in entry.iteritems() if key not in ignore])


def csv_write(data):
  '''output a list of dictionaries as a csv file'''

  # e.g. "AskReddit__20-Apr-16__00-04-AM"
  now = datetime.datetime.now()
  filename_ts = now.strftime("%d-%b-%y__%H-%M-%p")
  filename = "AskReddit__" + filename_ts  # TODO: magic strings are bad

  with open(filename + ".csv", 'wb') as csvfile:
      fieldnames = data[0].keys()
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

      writer.writeheader()

      for post in data:
        writer.writerow(post)