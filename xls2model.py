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

    # Read the species sheet
    species_df = pd.read_excel(xlsfilename, sheet_name='species') # what about csv?
    
    # Extract Species ID, Species Name, and Species Parameters
    speciesIDs = species_df.iloc[1:, 1].str.strip()  # Species ID in column B
    speciesNames = species_df.iloc[1:, 2]  # Species Name in column C
    speciesParams = species_df.iloc[1:, 3:6] # Y0, Ymax, tau parameters
    
    # Read the reactions sheet
    reactions_df = pd.read_excel(xlsfilename, sheet_name='reactions')
    
    # Extract Reaction IDs, Reaction Rules, and Reaction Parameters
    reactionIDs = reactions_df.iloc[1:, 1]  # Start Row 2, Column B
    reactionRules = reactions_df.iloc[1:, 2]  # Start Row 2, Column C
    reactionParams = reactions_df.iloc[1:,3:6] # w, n, and EC50 parameters
    
    modelName = xlsfilename.strip('.xlsx')
    mymodel= NetfluxModel(modelName,speciesIDs,speciesNames,speciesParams,reactionIDs,reactionRules,reactionParams)
    mymodel = createInteractionMatrix(mymodel)
    
    #print(f"DEBUG/createModel: mymodel: {mymodel}")
    #print(f"DEBUG/createModel: Species IDs: {mymodel.speciesIDs.tolist()}")
    #print(f"DEBUG/createModel: Reaction Rules: {mymodel.reactionRules.tolist()}")
    
    return mymodel

def createInteractionMatrix(model):
    # Creates n x m interaction matrix from reactionRules
    # Called by createModel()
    
    # Initialize interaction matrix and not matrix
    interaction_matrix = np.zeros((len(model.speciesIDs), len(model.reactionRules)))
    not_matrix = np.zeros((len(model.speciesIDs), len(model.reactionRules)))

    # Fill interaction matrix
    for i, rule in enumerate(model.reactionRules, start=1):
        #print(f"DEBUG/createInteractionMatrix: reaction:{rule}")
        reactants, product = rule.split('=>') # only 1 product allowed
        reactants = reactants.split('&')
        #print(f"DEBUG/createInteractionMatrix: reactants:{reactants}") # parsing problems here sometimes caused by use of "+" instead of "&"
        
        for reactant in reactants:
            reactant = reactant.strip()
            if reactant:
                #print(f"DEBUG/createInteractionMatrix: reactant:{reactant}")
                reactantID = model.speciesIDs.index[model.speciesIDs == reactant.strip('!')][0] # remove ! for inhibiting reactants (FIXME: prolbem if there is no element 0?)
                if '!' in reactant:
                    not_matrix[reactantID-1, i-1] = 1 # reactant is inhibiting
                interaction_matrix[reactantID-1, i-1] = -1  # add reactant; subtracting because indexing on species and rules starts at 1
        
        product = product.strip()
        if product:
#            print(['product:',product]) # FOR DEBUG
            productID = model.speciesIDs.index[model.speciesIDs == product][0]
            interaction_matrix[productID-1, i-1] = 1  # add product
    
    model.interactionMatrix = interaction_matrix
    model.notMatrix = not_matrix
    
    return model

#mymodel = createModel('exampleNet.xlsx') // TEMP when testing

# Debugging lines
# # Display the extracted data
# print(f"DEBUG/createModel: mymodel: {mymodel}")
# print(f"DEBUG/createModel: Species IDs: {mymodel.speciesIDs.tolist()}")
# print(f"DEBUG/createModel: Species Names: {mymodel.speciesNames.tolist()}")
# print(f"DEBUG/createModel: Reaction IDs: {mymodel.reactionIDs.tolist()}")
# print(f"DEBUG/createModel: Reaction Rules: {mymodel.reactionRules.tolist()}")
# print(f"DEBUG/createModel: Interaction Matrix: {mymodel.interactionMatrix.tolist()}")
# print(f"DEBUG/createModel: Not Matrix: {mymodel.notMatrix.tolist()}")


