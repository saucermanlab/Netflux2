Netflux2 development notes
Updated 3/24/2025, version: alpha2
by Jeff Saucerman

version alpha2: export models in Python or XGMML formats
version alpha1: functional webapp, loads models, runs simulations, runs on 
    PythonAnywhere at netflux.pythonanywhere.com

Netflux2 requires installation of:
flask, flask-session >=0.6, numpy, matplotlib, scipy
Install flask-session with: conda install conda-forge::flask-session to get v0.6
or pip3 install Flask-sesssion to get 0.8

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
model2xgmml.py
    interaction_matrix_to_xgmml(model) writes network in XGMML format. Not yet tested
    in Cytoscape and likely needs further work.
webapp.py 
    Web interface similar to the original Netflux
    Currently it loads exampleNet, can run complex simulations, replot
    openmodel() opens file dialog, creates NetfluxModel, reactionParams, speciesParams, speciesIDs, reactionRules
    downloadmodel() writes 3 files to uploads, then downloads them in browser
    downloadxgmml() calls model2xgmml, writes xgmml, then downloads it from browser
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
Hosting on pythonanywhere.com
        It's working!
        I had to put the 'uploads' and 'models' folders directly under "netflux"
        in console: pip3 install Flask-session

Netflux file formatting errors:
Should start input reaction as '=> A'
Single space separating variables or operators
Represent AND gates with '&'. Use of '+' is deprecated.
Represent OR gates as separate reactions on separate lines, e.g. 'A => C','B => C'
Inhibition '!' is used only for reactants.

To do:
Cleanup- clear ploads directory at start, clear flask session data
Error handling

Planned features:
Update XGMML if given a previous one
Cytoscape integration?
Model library
Include more advanced codes for sensitivity analysis,  validation, parameter estimation?

Flask programming tips:
- Copilot very helpful
- passing numpy arrays to the web causes an internal server error, hard to debug
- convert numpy arrays to lists with .tolist()
- Spyder can't debug Flask, so I use lots of print statements:
print(f"DEBUG/updateReactionParams: updated reaction: {selectedReaction}, w: {w}, ec50: {ec50}, n: {n}")
- session variables with session
- server-side session variables with flask_session
- Flask g for "thread global" variables- used for ODEfunc handle

