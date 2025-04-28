# xls2model.py
# 1/18/2025 created by Jeff Saucerman
# Imports XLS in Netflux syntax, creates internal representation of model of Netflux model
# This is based roughly on xls2Netflux.m
#
# A NetfluxModel has attributes: modelName, speciesIDs, speciesNames, reactionIDs, reactionRules, reactionParams, interactionMatrix, notMatrix
# speciesParameters contains: Y0, Ymax, tau parameters
# reactionParameters contains: w, n, and EC50 parameters
import numpy as np
import pandas as pd
import os, traceback, re

# internal representation of a Netflux2 model
class NetfluxModel:
  def __init__(self, modelName, speciesIDs, speciesNames, speciesParams, reactionIDs, reactionRules, reactionParams):
    self.modelName = modelName
    self.speciesIDs = speciesIDs
    self.speciesNames = speciesNames
    self.speciesParams = speciesParams
    self.reactionIDs = reactionIDs
    self.reactionRules = reactionRules
    self.reactionParams = reactionParams

def createModel(xlsfilename):
    # creates the NetfluxModel from the spreadsheet in Netflux syntax
    try:
        # Read the species sheet
        species_df = pd.read_excel(xlsfilename, sheet_name='species') # what about csv?
        
        # Extract Species ID, Species Name, and Species Parameters
        speciesIDs = species_df.iloc[1:, 1].str.strip()  # Species ID in column B
        speciesNames = species_df.iloc[1:, 2]  # Species Name in column C
        speciesParams = species_df.iloc[1:, 3:6] # Y0, Ymax, tau parameters
        #print(f"speciesIDs:{speciesIDs}, speciesNames:{speciesNames}, speciesParams:{speciesParams}")
        
        # Read the reactions sheet
        reactions_df = pd.read_excel(xlsfilename, sheet_name='reactions')
        
        # Extract Reaction IDs, Reaction Rules, and Reaction Parameters
        reactionIDs = reactions_df.iloc[1:, 1]  # Start Row 2, Column B
        reactionRules = reactions_df.iloc[1:, 2]  # Start Row 2, Column C
        reactionParams = reactions_df.iloc[1:,3:6] # w, n, and EC50 parameters
        #print(f"reactionIDs:{reactionIDs}, reactionRules:{reactionRules}, reactionParams:{reactionParams}")
        
        modelName = os.path.basename(xlsfilename).strip('.xlsx')
        mymodel= NetfluxModel(modelName,speciesIDs,speciesNames,speciesParams,reactionIDs,reactionRules,reactionParams)
    
    # Add more error handling?
    except FileNotFoundError as e:
        print(f"{xlsfilename} not found: {e}")
        raise
    try:  
        mymodel = createInteractionMatrix(mymodel)
        #print(f"xls2model/createModel: interaction_matrix: {mymodel.interactionMatrix}")
    except Exception as e:  
        print(f"Error in calling xls2model.createModel calling createInteractionMatrix: {e}") # captures errors raised in createInteractionMatrix
        raise
    
    # Debugging lines
    # # Display the extracted data
    # print(f"DEBUG/createModel: mymodel: {mymodel}")
    # print(f"DEBUG/createModel: Species IDs: {mymodel.speciesIDs.tolist()}")
    # print(f"DEBUG/createModel: Species Names: {mymodel.speciesNames.tolist()}")
    # print(f"DEBUG/createModel: Reaction IDs: {mymodel.reactionIDs.tolist()}")
    # print(f"DEBUG/createModel: Reaction Rules: {mymodel.reactionRules.tolist()}")
    # print(f"DEBUG/createModel: Interaction Matrix: {mymodel.interactionMatrix.tolist()}")
    # print(f"DEBUG/createModel: Not Matrix: {mymodel.notMatrix.tolist()}")
    
    return mymodel

def createInteractionMatrix(mymodel):
    # Creates n x m interaction matrix from reactionRules
    # createInteractionMatrix is called by createModel()
    # 4/2025: handles both old syntax (A & !B => C) and new syntax (A AND NOT B -> C)
    
    # Initialize interaction matrix and not matrix
    speciesIDs = mymodel.speciesIDs.tolist()
    reactionIDs = mymodel.reactionIDs.tolist()
    reactionRules = mymodel.reactionRules.tolist()
    interaction_matrix = np.zeros((len(speciesIDs), len(reactionRules)))
    not_matrix = np.zeros((len(speciesIDs), len(reactionRules)))
    try:
        # Fill interaction matrix
        for i, rule in enumerate(reactionRules, start=0):
            #print(f"DEBUG/createInteractionMatrix: reactionID:{reactionIDs[i]}, reaction:{rule}")
            reactants, product = re.split(r'->|=>', rule) # split with => or -> ; only 1 product allowed
            #print(f"DEBUG/createInteractionMatrix: reactants:{reactants}") # parsing problems here sometimes caused by use of "+" instead of "&"
            
            reactants = re.split(r'&|AND', reactants) # OLD CODE: reactants.split('&')
            #print(f"DEBUG/createInteractionMatrix: reactants:{reactants}") # parsing problems here sometimes caused by use of "+" instead of "&"
            
            for reactant in reactants:
                reactant = reactant.strip()
                if reactant: 
                    if '!' in reactant or 'NOT' in reactant:        # handles old !X or new NOT X syntax
                        reactant = reactant.replace('!', '')       
                        reactant = reactant.replace('NOT ', '')    
                        reactantNum = speciesIDs.index(reactant)    
                        not_matrix[reactantNum, i] = 1 # reactant is inhibiting
                    else:
                        reactantNum = speciesIDs.index(reactant) 
                    interaction_matrix[reactantNum, i] = -1  # add reactant
            #print(f"DEBUG/createInteractionMatrix: reactant:{reactant}")   
            
            product = product.strip()
            if product:
                #print(f"DEBUG/createInteractionMatrix: product: {product}")
                productNum = speciesIDs.index(product)
                interaction_matrix[productNum, i] = 1  # add product
            #print(f"DEBUG/xls2model/createInteractionMatrix: reaction {rule}, reactant:{reactant}, product:{product}")
    
    except (ValueError, IndexError) as e:
        lineno = traceback.extract_tb(e.__traceback__)[-1].lineno
        print(f"Error in xls2model.createInteractionMatrix on line {lineno}: :{e}")
        error_message = f"{type(e).__name__} reading reaction {reactionIDs[i]}:{rule}, reactant:{reactant}, product:{product}. "
        raise Exception(error_message) from e
    
    #print(f"createInteractionMatrix: {interaction_matrix}")
    mymodel.interactionMatrix = interaction_matrix
    mymodel.notMatrix = not_matrix
    #print("DEBUG: at bottom of createInteractionMatrix")
    return mymodel
    
# for debugging xls2model.createInteractionMatrix in isolation
if __name__ == "__main__":

    # # testing with model: ['A & B => C', 'B => A']
    # # current error on line 80
    # mymodel = NetfluxModel("net",[],[],[],[],[],[])
    # mymodel.speciesIDs = np.array(['A','B','C'])
    # #mymodel.reactionRules = np.array(['A & B => C', 'B => A'])
    # mymodel.reactionRules = np.array(['A AND NOT B => C', 'B => A'])
    # mymodel = createInteractionMatrix(mymodel)
    
    # testing with exampleNet
    mymodel = createModel('exampleNet_error.xlsx') # testing
    
    print(f"interactionMatrix: {mymodel.interactionMatrix}")
    print(f"notMatrix: {mymodel.notMatrix}")





