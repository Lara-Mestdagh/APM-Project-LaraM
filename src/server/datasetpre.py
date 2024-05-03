import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

class Dataset:
    def __init__(self, file_path):
        self.dataset = pd.read_csv(file_path, dtype={
            'Name': 'str', 'Species': 'str', 'Gender': 'str', 'Personality': 'str', 'Hobby': 'str'})        
            # Make sure these are read as string
        print(f"Initial dataset shape: {self.dataset.shape}")


    def preprocess_data(self):
        # Check for a large number of empty rows before removing
        if self.dataset.isnull().sum().sum() > 100:
            self.dataset = self.dataset.dropna()
        print(f"Shape after removing empty rows: {self.dataset.shape}")

        # Analyze dataset for incorrect values using describe
        print(self.dataset.describe(include='all'))

        # Drop unnecessary columns
        drop_cols = ['Favorite Song', 'Style 1', 'Style 2', 'Color 1', 'Color 2', 'Wallpaper', 'Flooring', 'Furniture List', 'Filename']
        self.dataset = self.dataset.drop(columns=drop_cols)

        # Convert Birthday to datetime and split into day and month
        self.dataset['Birthday'] = pd.to_datetime(self.dataset['Birthday'], format='%d-%b')
        self.dataset['Birth Month'] = self.dataset['Birthday'].dt.month
        self.dataset['Birth Day'] = self.dataset['Birthday'].dt.day

        # Check for duplicate rows
        duplicates = self.dataset.duplicated()
        print(f"Found {duplicates.sum()} duplicates")

        # Drop duplicate rows if unjustifiable
        self.dataset = self.dataset[~duplicates]

        print(f"Final dataset shape after preprocessing: {self.dataset.shape}")
        return self.dataset


    # A heatmap of the Species and Personality
    def species_personality_heatmap(self):
        species_personality = pd.crosstab(self.dataset['Species'], self.dataset['Personality'])
        sns.heatmap(species_personality, cmap='coolwarm')
        plt.title('Species and Personality')
        plt.show()


    # A boxplot of the Species vs Personality
    def analyze_boxplots(self):
        sns.boxplot(x='Species', y='Personality', data=self.dataset)
        plt.title('Boxplot of Species vs Personality')
        plt.show()