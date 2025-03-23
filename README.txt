Netflux2 development notes
Updated 3/15/2025, version: alpha1
by Jeff Saucerman

Netflux2 requires installation of:
flask, flask-session >=0.6, numpy, matplotlib, scipy
Install flask-session with: conda install conda-forge::flask-session to get v0.6

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
webapp.py 
    Web interface similar to the original Netflux
    Currently it loads exampleNet, can run complex simulations, replot
    openmodel() opens file dialog, creates NetfluxModel, reactionParams, speciesParams, speciesIDs, reactionRules
    simulate() loads the ODEfunc, params, runs either new or continued simulations
    create_plot() takes the selected variables, t, and y and makes a plot
    replot() runs create_plot() again (needed?)
    resetparams() runs when you click Reset Parameters, resets speciesParams and reactionParams
    resetsim() runs when you click Reset Simulation, resets t and y
    updateSpeciesParams() runs when you change a species parameter value, updates speciesParams
    updateReactionParams() runs when you change a reaction parameter value, updates reactionParams
    getSelectedSpeciesParams() runs when you select a different species, updates fields for y0/ymax/tau 
    getSelectedReactionParams() runs when you select a different reaction, updates fields for w/ec50/n
index.html
    style parameters
    navbar, including toggleMenu(): openmodel(), help(), about()
    time span field
    multiple select "variables": selects which variable will be plotted in openmodel()
    simulate/replot/resetparams/resetsim buttons -> simulate()/replot()/resetparams()/resetsims() functions
    status label
    species parameter select: changing this calls getSelectedSpeciesParams()
    species parameter fields y0, ymax, tau. updating calls updateSpeciesParams() 
    reaction parameter select: changing this calls getSelectedReactionParams()
    reaction parameter fields w, ec50, n. updating calls updateReactionParams()
       
To do: 
Some bugs regarding updating parameters in complex simulations.
Bug in updated status message- shows reset parameters but not simulation completed
Testing with other network models
Model exporting through webapp

Flask programming tips:
- Copilot very helpful
- passing numpy arrays to the web causes an internal server error, hard to debug
- convert numpy arrays to lists with .tolist()
- Spyder can't debug Flask, so I use lots of print statements:
print(f"DEBUG/updateReactionParams: updated reaction: {selectedReaction}, w: {w}, ec50: {ec50}, n: {n}")
- session variables with session
- server-side session variables with flask_session
- Flask g for "thread global" variables- used for ODEfunc handle

