Netflux2 model library notes
Updated 3/25/2025 by Jeff Saucerman

exampleNet
    loads correctly in Python and webapp, basic simulations OK
    need to test changes in other parameters

Kraeutler2010_betaAdrenergic.xlsx
    Replaced old "+" syntax with "&" syntax
    loads correctly from Python and webapp
        adjusted => PP1 w = 1 to prevent auto-activation of PKAC
        adjusted => PP2A w = 1 to prevent auto-activation of TnI, RyR

Ryall2012_cardiomyocyte_hypertrophy.xlsx
    loads correctly from Python and webapp, simulations look good  

Zeigler2016_cardiac_fibroblast.xslx
    loads correctly from Python and webapp, simulations look good

Liu2021_macrophage.xlsx
	not yet tested
    
    
Notes:
If you want to run the "test" files here, copy xls2model, model2PythonODE into his folder. Or use relative or absolute imports.
module_path = '/path/to/your/module_directory'
# Add the directory to sys.path
sys.path.insert(0, module_path)


More testing needed on "if x<0: x = 0" in act()
Some issues of parameters not resetting when loading a second model.
The order of n and EC50 were swapped in some places. Fixed but check this more