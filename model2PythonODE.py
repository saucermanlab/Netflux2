# model2PythonODE.py
# by Jeff Saucerman
# 3/25/2025 JS: fixed bug about scalar power in act(), set x<0 to 0
# 3/24/2025 JS: fixed bug for multiple AND reactions in rcnStringList
# 3/15/2025 JS: modified to use io.StringIO instead of file.write
# 1/20/2025 JS: ported from MATLAB versions
# replicates features of exportPythonODE.m and Netflux2PythonODE.m
# STATUS: 
# BUG: <string>:201: RuntimeWarning: invalid value encountered in scalar power
#   This seems to do with the powers in the act function- potential bug.

import numpy as np
import datetime
import io

def returnModelFuncs(model):
# Returns loadParamFunc and ODEfunc as handles, runScript as ioString object
    paramsFileText = generateParamsFile(model)
    exec(paramsFileText) 
    loadParamsFunc = locals()['loadParams'] # generates function handle

    runScript = generateRunFile(model)

    ODEfileText = generateODEfile(model)
    exec(ODEfileText,globals())   # had bug unless I put ODEfileText in globals
    ODEfunc = globals()['ODEfunc']
    
    return loadParamsFunc, runScript, ODEfunc


def writeModel(model):
# Writes modelname_params.py, modelname_run.py, modelname_ODEs.py
# confirmed working for exampleNet, 3/15/2025
    paramsFileText = generateParamsFile(model)
    filename = str(model.modelName) + "_params.py"
    with open(filename, 'w') as file:
        file.write(paramsFileText)
    print(f"Netflux2 wrote {filename}")
    
    runFileText = generateRunFile(model)
    filename = str(model.modelName) + "_run.py"
    with open(filename, 'w') as file:
        file.write(runFileText)
    print(f"Netflux2 wrote {filename}")
    
    ODEfuncText = generateODEfile(model)
    filename = str(model.modelName) + "_ODEs.py"
    with open(filename, 'w') as file:
        file.write(ODEfuncText)
    print(f"Netflux2 wrote {filename}")

def generateParamsFile(model):
# Takes an LDEmodel and writes modelName_params.py, which will be loaded
# by modelName_run.py
# confirmed working for exampleNet, 3/15/2025
    
    output = io.StringIO()
    filename = str(model.modelName) + "_params.py"
    output.write(f"# {filename}\n")
    output.write(f"# Automatically generated by Netflux2 on {datetime.date.today()}\n")
    output.write("import numpy as np\n\n")
    output.write("def loadParams():\n")
    output.write("    # species parameters\n")
    output.write(f"    speciesIDs = {model.speciesIDs.tolist()}\n") 
    y0 = model.speciesParams.iloc[:,0].tolist()
    ymax = model.speciesParams.iloc[:,1].tolist()
    tau = model.speciesParams.iloc[:,2].tolist()
    output.write(f"    y0 = np.array({y0})\n")
    output.write(f"    ymax = np.array({ymax})\n")
    output.write(f"    tau = np.array({tau})\n\n")
    output.write("    # reaction parameters\n")
    w = model.reactionParams.iloc[:,0].tolist()
    n = model.reactionParams.iloc[:,1].tolist()
    EC50 = model.reactionParams.iloc[:,2].tolist()
    output.write(f"    w = np.array({w})\n")
    output.write(f"    n = np.array({n})\n")
    output.write(f"    EC50 = np.array({EC50})\n\n")
    output.write("    return speciesIDs, y0, ymax, tau, w, n, EC50")
    return output.getvalue() # returns paramsFileText
        
def generateRunFile(model):
    # Takes a NetfluxModel and writes modelName_run.py, which runs the simulation
    # Confirmed working 3/15/2025
    
    output = io.StringIO()
    fname = str(model.modelName) + "_run.py"
    output.write(f"# {fname}\n")
    output.write(f"# Automatically generated by Netflux2 on {datetime.date.today()}\n")
    output.write("import numpy as np\n")
    output.write("from scipy.integrate import solve_ivp\n")
    output.write("import matplotlib.pyplot as plt\n")
    output.write(f"import {model.modelName}_ODEs\n")
    output.write(f"import {model.modelName}_params\n\n")
    output.write(f"speciesNames, y0, ymax, tau, w, n, EC50 = {model.modelName}_params.loadParams()\n\n")        
    output.write("# Run single simulation\n")
    output.write("tspan = [0, 10]\n")
    output.write(f"solution = solve_ivp({model.modelName}_ODEs.ODEfunc, tspan, y0, rtol=1e-8, args=(ymax, tau, w, n, EC50))\n\n")
    output.write("fig, ax = plt.subplots()\n")
    output.write("ax.plot(solution.t,solution.y.T)\n")
    output.write("ax.set(xlabel='Time',ylabel='Normalized activity')\n")
    output.write("ax.legend(speciesNames)\n")
    output.write("plt.show()")
    return output.getvalue() # returns runFileText

def generateODEfile(model):
    # writes the ODEs as logic-based differential equations
    # called by modelname_run.py
    # confirmed working for write mode, but BUG for interactive mode can't find ODEfunc 3/15/2025
    
    output = io.StringIO()
    filename = model.modelName + "_ODEs.py"
    output.write(f"# {filename}\n")
    output.write(f"# Automatically generated by Netflux2 on {datetime.date.today()}\n")
    output.write("import numpy as np\n\n")
    output.write("def ODEfunc(t,y,ymax,tau,w,n,EC50):\n\n")

    # name the indices by speciesID
    output.write("    # network species\n")
    for i, speciesID in enumerate(model.speciesIDs):
        output.write(f"    {speciesID} = {i}\n")

    output.write("\n    # logic-based differential equaations\n")
    output.write(f"    dydt = np.zeros({i+1})\n")      
    for speciesNum, speciesID in enumerate(model.speciesIDs):
        # print(f"DEBUG/model2PythonODE/generateODEfile: speciesNum:{speciesNum}, speciesID:{speciesID}")
        rcnString = getReactionString(model,speciesNum) # potential BUG: might also need to modify ymax for AND gates?
        #print(f"DEBUG/model2PythonODE: rcnString:{rcnString}")
        output.write(f"    dydt[{speciesID}] = ({rcnString}*ymax[{speciesID}] - y[{speciesID}])/tau[{speciesID}]\n")
    output.write("\n    return dydt\n")
    output.write(returnUtilityFunctions()) # writes the AND/OR/fact/finhib functions
    return output.getvalue() # returns ODEfuncText

def getReactionString(model,speciesNum):
    # generates strings for the reactions for which speciesNum is a product
    # utility function for writeODEfile
    #print(f"DEBUG/getReactionString: speciesID:{model.speciesIDs[speciesNum+1]}")

    # find reactions where speciesNum is a product
    intMat = model.interactionMatrix
    notMat = model.notMatrix
    rcnsWhereSpeciesIsProduct = np.where(intMat[speciesNum, :] == 1)[0].tolist()
    #print(f"DEBUG/getReactionString: speciesID:{model.speciesIDs[speciesNum+1]}, rcnsWhereSpeciesIsProduct: {rcnsWhereSpeciesIsProduct}")
    
    # loop over rcnsWhereSpeciesIsProduct to generate rcnStringList
    
    rcnStringList = []  # list of reactions where speciesNum is a product
    for rcnID in rcnsWhereSpeciesIsProduct:    
        reactantIndices = np.where(intMat[:,rcnID] == -1)[0].tolist() 
        if len(reactantIndices) == 0:           # input reaction, no reactants
            rcnStringList.append(f"w[{rcnID}]")
 
        elif len(reactantIndices) == 1:         # single reactant
            reactant = reactantIndices[0]
            if notMat[reactant,rcnID] == 0: # reactant is activating            
                rcnStringList.append(f"act(y[{model.speciesIDs[reactant+1]}],w[{rcnID}],n[{rcnID}],EC50[{rcnID}])")
            else:                                   # reactant is inhibiting
                rcnStringList.append(f"inhib(y[{model.speciesIDs[reactant+1]}],w[{rcnID}],n[{rcnID}],EC50[{rcnID}])")
        
        else:                                   
            rcnString = []
            for reactant in reactantIndices:    # multiple reactants 
                if notMat[reactant,rcnID] == 0: # reactant is activating            
                      rcnString.append(f"act(y[{model.speciesIDs[reactant+1]}],w[{rcnID}],n[{rcnID}],EC50[{rcnID}])")
                else:                                   # reactant is inhibiting
                      rcnString.append(f"inhib(y[{model.speciesIDs[reactant+1]}],w[{rcnID}],n[{rcnID}],EC50[{rcnID}])") # up to here is correct
            rcnStringList.append(f"AND(w[{rcnID}],[{','.join(rcnString)}])")  # BUG 3/25 potentially fixed but needs more testing

    #print(f"DEBUG/model2PythonODE/getReactionString: rcnStringList: {rcnStringList}") 
    if len(rcnStringList) == 1:
        rcnString = rcnStringList[0]
    else:
        rcnString = nestedOR(rcnStringList)
    # print(f"DEBUG/model2PythonODEgetReactionString: rcnString: {rcnString}")   
    return rcnString

def nestedOR(items):    
    if len(items) == 1:
        return items[0]
    else:
        return f"OR({items[0]},{nestedOR(items[1:])})"
        
def returnUtilityFunctions():
    # called by writeODEfile
    
    utilityFunctionText = """
# utility functions
def act(x, w, n, EC50):
    # hill activation function with parameters w (weight), n (Hill coeff), EC50
    if x < 0:   # BUG: needs more testing.
        x = 0 
    beta = ((EC50**n)-1)/(2*EC50**n-1)
    K = (beta-1)**(1/n)
    fact = w*(beta*x**n)/(K**n+x**n)
    if fact > w:
        fact = w
    return fact

def inhib(x, w, n, EC50):
    # inverse hill function with parameters w (weight), n (Hill coeff), EC50
    finhib = w - act(x, w, n, EC50)
    return finhib

def OR(x, y):
    # OR logic gate
    z = x + y - x*y
    return z

def AND(w, reactList):
    # AND logic gate, multiplying all of the reactants together
    if w == 0:
        z = 0
    else:
        p = np.array(reactList).prod()
        z = p/w**(len(reactList)-2)
    return z
"""    
    return utilityFunctionText
        




