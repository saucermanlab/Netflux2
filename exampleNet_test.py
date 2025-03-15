# test_exampleNet.py
# 3/15/20215 by Jeff Saucerman
# This file shows show to load a Netflux model and then write the Python ODE
# files or run the simulations interactively.
#
# write mode writes param, run, and ODE files to same directory as Netflux model
# interactive model loads and runs model without writing files
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import xls2model
import model2PythonODE

# load model                   
mymodel = xls2model.createModel('exampleNet.xlsx')

# # write mode
# model2PythonODE.writeModel(mymodel)

# interactive mode
# not sure that runScript is useful other than as quick verification model runs
loadParams, runScript, ODEfunc = model2PythonODE.returnModelFuncs(mymodel)

# # Can run basic simulation by directly running the auto-generated runScript
# exec(runScript)

# Or can run customized simulations by changing parameters 
[speciesIDs, y0, ymax, tau, w, n, EC50] = loadParams()
w[0] = 1    # turn on input to A
tspan = [0, 10]
solution = solve_ivp(ODEfunc, tspan, y0, args=(ymax, tau, w, n, EC50))

fig, ax = plt.subplots()
ax.plot(solution.t,solution.y.T)
ax.set(xlabel='Time',ylabel='Normalized activity')
ax.legend(mymodel.speciesNames)