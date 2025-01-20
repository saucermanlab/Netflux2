# test_exampleNet.py
# code for testing this file
import xls2model
import exportPythonODE
                   
mymodel = xls2model.createModel('exampleNet.xlsx')
exportPythonODE.writeModel(mymodel)

# now run exampleNet_run.py to simluate the network