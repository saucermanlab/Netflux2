# Netflux2
Netflux2 is a tool for modeling biological networks, in Python. *It is in early phases of development*, with a current focus of replicating features in the original Netflux (https://github.com/saucermanlab/Netflux), which is based in MATLAB.

## Planned features
- Accessing all main features of Netflux from a Python-only environment
- Running Netflux2 from notebooks
- Webapp to replace the original MATLAB GUI from Netflux
- Automated network generation
- Import/export with SBML-QUAL, XGMML

## What works right now
Use test_exampleNet.py to load exampleNet.xls, exporting Python ODE files. Then simulate the model with exampleNet_run.py to get this result:
![image](https://github.com/user-attachments/assets/af09ab2f-a873-4c59-a2d9-2b149c6c19bb)
exciting!

**Netflux2 has not been tested on other networks, bugs are likely.**

## Next steps
- Testing Netflux2 with other networks.
- Add error handling
- Look at updates made by Ali and Jamie to gate logic, activation functions
- add MATLAB ODE export?
- Discuss and add files from logicDE (https://github.com/saucermanlab/logicDE) that should come over to Neflux2
