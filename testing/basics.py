import pandas as pd
import matplotlib.pyplot as plt

# Load the CSV file to examine the data
file_path = "./data/Animal_Crossing_Villagers.csv"
villagers_data = pd.read_csv(file_path)

# make a graph based on the gender of the villagers
data = villagers_data['Gender'].value_counts()
data.plot(kind='bar', color=['blue', 'red'])  # switch to vertical bar plot
plt.title('Visual Representation of Villager by Gender')
plt.xlabel("Gender")  # switch x and y labels
plt.ylabel("Number of Villagers")
plt.show()
