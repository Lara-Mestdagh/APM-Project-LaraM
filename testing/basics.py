import pandas as pd
import calendar

import matplotlib.pyplot as plt

# Load the CSV file to examine the data
file_path = "./data/Animal_Crossing_Villagers.csv"
villagers_data = pd.read_csv(file_path)

# Extract the month from the 'Birthday' column
villagers_data['Month'] = pd.to_datetime(villagers_data['Birthday'], format='%d-%b').dt.month

# Count the occurrences of each month
month_counts = villagers_data['Month'].value_counts()

# Sort the months in ascending order
month_counts = month_counts.sort_index()

# Plot the graph horizontally
plt.barh(month_counts.index, month_counts.values, tick_label=[calendar.month_name[i] for i in month_counts.index])
plt.xlabel('Count')
plt.ylabel('Month')
plt.title('Birthdays per Month')
plt.show()
