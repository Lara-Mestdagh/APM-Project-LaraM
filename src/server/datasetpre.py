import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class Dataset:
    def __init__(self, file_path):
        self.dataset = pd.read_csv(file_path, dtype={
            'Name': 'str', 'Species': 'str', 'Gender': 'str', 'Personality': 'str', 'Hobby': 'str'})

    def preprocess_data(self):
        # Drop rows with missing values
        self.dataset = self.dataset.dropna()
        # Convert Birthday to datetime
        self.dataset['Birthday'] = pd.to_datetime(self.dataset['Birthday'], format='%d-%b')
        # Drop unnecessary columns
        drop_cols = ['Favorite Song', 'Style 1', 'Style 2', 'Color 1', 'Color 2', 'Wallpaper', 'Flooring', 'Furniture List', 'Filename']
        self.dataset = self.dataset.drop(columns=drop_cols)
        # Check for duplicate rows
        duplicates = self.dataset.duplicated()
        # Drop duplicate rows
        self.dataset = self.dataset[~duplicates]
        
        return self.dataset

    def species_personality_heatmap(self):
        species_personality = pd.crosstab(self.dataset['Species'], self.dataset['Personality'])
        sns.heatmap(species_personality, cmap='coolwarm')
        plt.title('Species and Personality')
        plt.show()