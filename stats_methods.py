##################
# Things to find:
# Average, Std Deviation
# Graphs:
# Bar graph of gas used (rounded) vs num blocks that used that gas
import pandas as pd
import numpy as np

def organize_data():
    file = open('new_data/arbitrage_100.txt', 'r')
    data = file.readlines()

    new_data = {}
    #gets all the distinct gasUsed
    for line in data:
        split_line = line.split('|')
        new_data[float(split_line[0])] = int(split_line[-1])

    return new_data

def get_average(data):
    sum = 0
    for perc in data.keys():
        sum+=perc

    return sum/len(data)

def find_max(data):
    max = -1

    for perc in data.keys():
        if perc > max:
            max = perc

    return max

def find_min(data):
    min = 100000
    for perc in data.keys():
        if perc < min:
            min = perc 

    return min

data = organize_data()
average = get_average(data)

max_percent = find_max(data)
min_percent = find_min(data)

print(average)
print(max_percent)
print(min_percent)
