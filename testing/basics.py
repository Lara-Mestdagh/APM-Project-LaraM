import pandas as pd
import calendar

import matplotlib.pyplot as plt

# Load the CSV file to examine the data
file_path = "./data/Animal_Crossing_Villagers.csv"
villagers_data = pd.read_csv(file_path)

# using species, birthday, personality and hobby let's filter villagers
# if it is none, it means we don't want to filter by that attribute

def filter_villagers(species=None, birthday=None, personality=None, hobby=None):
    filtered_data = villagers_data
    if species:
        filtered_data = filtered_data[filtered_data['Species'] == species]
    if birthday:
        filtered_data = filtered_data[filtered_data['Birthday'].str.contains(birthday)]
    if personality:
        filtered_data = filtered_data[filtered_data['Personality'] == personality]
    if hobby:
        filtered_data = filtered_data[filtered_data['Hobby'] == hobby]
    return filtered_data

