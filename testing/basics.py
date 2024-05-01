import pandas as pd
import calendar

import matplotlib.pyplot as plt

# Load the CSV file to examine the data
file_path = "./data/Animal_Crossing_Villagers.csv"
villagers_data = pd.read_csv(file_path)

# Graphs showing all catchphrases by beginning letter, amount of words, and amount of letters.
# Catchphrases by beginning letter
catchphrase_letter = villagers_data["Catchphrase"].str[0].str.upper()
catchphrase_letter = catchphrase_letter.value_counts().sort_index()
catchphrase_letter.plot(kind="bar")
plt.title("Catchphrases by beginning letter")
plt.xlabel("Letter")
plt.ylabel("Amount")
plt.show()

# Catchphrases by amount of words
catchphrase_words = villagers_data["Catchphrase"].str.split().str.len()
catchphrase_words = catchphrase_words.value_counts().sort_index()
catchphrase_words.plot(kind="bar")
plt.title("Catchphrases by amount of words")
plt.xlabel("Amount of words")
plt.ylabel("Amount")
plt.show()

# Catchphrases by amount of letters
catchphrase_letters = villagers_data["Catchphrase"].str.len()
catchphrase_letters = catchphrase_letters.value_counts().sort_index()
catchphrase_letters.plot(kind="bar")
plt.title("Catchphrases by amount of letters")
plt.xlabel("Amount of letters")
plt.ylabel("Amount")
plt.show()