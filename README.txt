Netflux2 development notes
Updated 3/15/2025
by Jeff Saucerman

exampleNet.xls: example Netflux model
exampleNet_test.py: shows how to load Netflux model, run in write or interactive mode
xls2model.py
    Loads Netflux model (xls file format)
    class LDEModel, with attributes speciesNames, ....
    createModel(xlsfilename) returns an LDEModel called mymodel
    createInteractionMatrix(model) adds interaction_matrix and not_matrix to model
    mymodel = createModel('exampleNet.xlsx') # is hard-coded currently
model2PythonODE.py
    writeModel(model) calls writeParamsFile, writeRunFile, writeODEfile
    writeParamsFile writes modelName_params.py
    writeRunFile writes modelName_run.py
    writeODEfile writes modelName_ODEs.py
    utility functions for writeODEfile:
        getReactionString(model,speciesID) creates reaction strings for ODE file
        nestedOR nests reactions for OR gates
        returnUtilityFunctions contains the code for act/inhib/AND/OR
       
To do: 
Prototype Netflux webapp
Refactoring to be me more object oriented.
