from setuptools import setup, find_packages

# Function to read the requirements from the requirements.txt file
def read_requirements():
    try:
        with open('requirements.txt', 'r') as req:
            content = req.read()
            requirements = content.strip().split('\n')
            # Remove empty lines or comments
            requirements = [line for line in requirements if line and not line.startswith('#')]
        return requirements
    except FileNotFoundError:
        print("Error: 'requirements.txt' not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

setup(
    name='APM Thuisproject',  
    description='Ontwikkeling multi-client-server toepassing in Python met als input een dataset afkomstig van Kaggle.com',  
    url='https://github.com/Lara-Mestdagh/APM-Project-LaraM',  # URL to repository
    author='Lara Mestdagh', 
    author_email='lara.mestdagh@student.howest.be', 
    license='MIT',                          # De licentie waaronder je project valt
    packages=find_packages(),               # Vind alle packages in de directory
    install_requires=read_requirements(),   # Reads requirements from requirements.txt
    classifiers=[
        'Development Status :: 3 - Alpha',                  # Current development status
        'Intended Audience :: Education',                   # Target audience
        'Intended Audience :: Science/Research',            # Additional audience
        'License :: OSI Approved :: MIT License',           # License
        'Programming Language :: Python :: 3',              # Supported Python versions
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Mathematics',   # Specific topic
    ],
    python_requires='>=3.6',  # Minimale vereisten voor de Python versie
)
