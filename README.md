# Data Processing Pipeline

This project parses a folder of input files and converts them into a unified pandas DataFrame for analysis.  
The pipeline first reads all files using `folder_parser.py`, which combines them into a single raw DataFrame.  
Hereafter the code transform each dataframe for proper methodes, and ready to be plotted by the plotpy file. 
These methods include the **ACER method**, **CNEC hours**, **market ratio**, **France method**, and **shadow price analysis**.  
Each method runs independently and produces its own output DataFrame.  
The project structure separates parsing, transformations, analysis logic..  
All result DataFrames are handled by functions under the `compliance_methods/`, which writes outputs to files.  

This modular design makes it easy to extend the pipeline with additional parsing steps or analysis methods.

Use the compliance_visualizations.ipynb for examples on how to use the method, and in depth analysis of compliance