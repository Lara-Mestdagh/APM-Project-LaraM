from setuptools import setup, find_packages

setup(
    name='MijnProject',  # Naam van je project
    version='0.1.0',  # De huidige versie van je project
    description='Een gedetailleerde beschrijving van mijn project',  # Een korte beschrijving van je project
    url='https://github.com/jouwgebruikersnaam/mijnproject',  # URL naar de repository
    author='Jouw Naam',  # Je naam
    author_email='jouw.email@example.com',  # Je contact email
    license='MIT',  # De licentie waaronder je project valt
    packages=find_packages(),  # Vind alle packages in de directory
    install_requires=[
        'numpy',  # Een voorbeeld van een afhankelijkheid
        'pandas',  # Nog een voorbeeld van een afhankelijkheid
    ],
    entry_points={
        'console_scripts': [
            'mijnscript=mijnpackage.mijnmodule:main',  # Hiermee kun je command-line scripts definiëren
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',  # De huidige status van je project
        'Intended Audience :: Developers',  # Het beoogde publiek
        'License :: OSI Approved :: MIT License',  # De licentie
        'Programming Language :: Python :: 3',  # De programmeertaal versie
        'Programming Language :: Python :: 3.7',
    ],
    python_requires='>=3.6',  # Minimale vereisten voor de Python versie
)
