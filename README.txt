Netflux (v2) development notes
Updated 3/30/2025, version: alpha2
by Jeff Saucerman

version alpha2: export models in Python or XGMML formats, simulation CSV, error handling, documentation
version alpha1: functional webapp, loads models, runs simulations, runs on 
    PythonAnywhere at netflux.pythonanywhere.com

Netflux (v2) requires installation of:
flask, flask-session >=0.6, numpy, matplotlib, scipy
Install flask-session with: conda install conda-forge::flask-session to get v0.6
or pip3 install Flask-sesssion to get 0.8

exampleNet.xls: example Netflux model
exampleNet_test.py: shows how to load Netflux model, run in write or interactive mode
xls2model.py
    Loads Netflux model (xlsx file format)
    class LDEModel, with attributes speciesNames, ....
    createModel(xlsfilename) returns an LDEModel called mymodel
    createInteractionMatrix(model) adds interaction_matrix and not_matrix to model
    Error handling:
        runs hard-coded models at bottom of xls2model.py if it is run directly
        try/catch around reactants/products not found in speciesIDs (line 72, 80)
            BUG: still need to elevate the error to webapp
    Updated syntax:
        Allows Netflux(v1) syntax: A & !B =>C as well as new Netflux(v2) syntax: A AND NOT B -> C
model2PythonODE.py
    writeModel(model) calls writeParamsFile, writeRunFile, writeODEfile
    writeParamsFile writes modelName_params.py
    writeRunFile writes modelName_run.py
    writeODEfile writes modelName_ODEs.py
    utility functions for writeODEfile:
        getReactionString(model,speciesID) creates reaction strings for ODE file
        nestedOR nests reactions for OR gates
        returnUtilityFunctions contains the code for act/inhib/AND/OR
model2xgmml.py
    interaction_matrix_to_xgmml(model) writes network in XGMML format. Now generates
    XGMML files that work in Cytoscape with style file "Netflux2 Cytoscape style.xml".
webapp.py 
    Web interface similar to the original Netflux
    Currently it loads exampleNet, can run complex simulations, replot
    openmodel() opens file dialog, creates NetfluxModel, reactionParams, speciesParams, speciesIDs, reactionRules
    downloadmodel() writes 3 files to uploads, then downloads them in browser
    downloadxgmml() calls model2xgmml, writes xgmml, then downloads it from browser
    downloadSimulation() loads model, t, y, writes csv, then downloads it from browser
    simulate() loads the ODEfunc, params, runs either new or continued simulations
    create_plot() takes the selected variables, t, and y and makes a plot
    replot() runs create_plot() again (needed?)
    resetparams() runs when you click Reset Parameters, resets speciesParams and reactionParams
    resetsim() runs when you click Reset Simulation, resets t and y
    updateSpeciesParams() runs when you change a species parameter value, updates speciesParams
    updateReactionParams() runs when you change a reaction parameter value, updates reactionParams
    getSelectedSpeciesParams() runs when you select a different species, updates fields for y0/ymax/tau 
    getSelectedReactionParams() runs when you select a different reaction, updates fields for w/ec50/n
    loadLibrary() loads library.xls into "library", which is stored as a session var
    getModelInfo() gets the description for the selectedModel from library
    sendSelectedModel() stores the name of selectedModel from library, stores as sesssion var
    getSelectedModel() gets the name of selectedModel from library
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
library.html
    browse pre-loaded models, open them in Netflux
Hosting on pythonanywhere.com
        I had to put the 'uploads' and 'models' folders directly under "netflux"
        in console: pip3 install Flask-session

Common Netflux file formatting errors:
Should start input reaction as '=> A'
Single space separating variables or operators
Represent AND gates with '&'. Use of '+' is deprecated.
Represent OR gates as separate reactions on separate lines, e.g. 'A => C','B => C'
Inhibition '!' is used only for reactants.
If there are no reactions going to a species, we put a 0.

To do:
Support missing input reactions to a species
Cleanup- clear uploads directory at start, clear flask session data
Error handling
more bug testing with model library, loading additional models

Planned features:
Update XGMML if given a previous one (from code, not in GUI)
Cytoscape integration?
Will keep advanced codes for sensitivity analysis,  validation, parameter estimation in logicDE

Flask programming tips:
- Copilot very helpful
- passing numpy arrays to the web causes an internal server error, hard to debug
- convert numpy arrays to lists with .tolist()
- Spyder can't debug Flask, so I use lots of print statements:
print(f"DEBUG/updateReactionParams: updated reaction: {selectedReaction}, w: {w}, ec50: {ec50}, n: {n}")
- session variables with session. Use these to pass vars between functions and pages
- server-side session variables with flask_session
- Flask g for "thread global" variables- used for ODEfunc handle