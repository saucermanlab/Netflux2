# model2xgmml.py:
# This file obtains intMat and notMat from my model and converts to XGMML
# Jeff Saucerman 3/30/2025

import xml.etree.ElementTree as ET
import os

def interaction_matrix_to_xgmml(mymodel, export_path=[]):
    modelName = mymodel.modelName
    interactionMatrix = mymodel.interactionMatrix
    notMatrix = mymodel.notMatrix
    speciesIDs = mymodel.speciesIDs.tolist()
    #reactionIDs= mymodel.reactionIDs.tolist()
    
    # Create the root element for XGMML
    root = ET.Element("graph", attrib={
        "label": modelName,
        "xmlns": "http://www.cs.rpi.edu/XGMML"
    })
    
    # Create a dictionary to store nodes
    nodes = {}
    
    # Iterate through the interaction matrix to create nodes and edges
    
    for j in range(interactionMatrix.shape[1]): # loop over species, j: species number, shape[1] is num species
        reactants = []
        products = []
        inhibitors = []
        
        for i in range(interactionMatrix.shape[0]): # loop over reactions; i: reaction number, shape[0] is num reactions
            if interactionMatrix[i, j] == -1:
                reactants.append(speciesIDs[i])
            elif interactionMatrix[i, j] == 1:
                products.append(speciesIDs[i]) # DEBUG, ERROR HERE
            if notMatrix[i, j] == -1:
                inhibitors.append(speciesIDs[i])
        
        # Create product nodes
        for product in products:
            if product not in nodes:
                node = ET.SubElement(root, "node", attrib={"id": product, "label": product})
                nodes[product] = node
        
        # Create reactant nodes and AND node if necessary
        if len(reactants) > 1:
            and_node_id = f"and_{j}"
            and_node = ET.SubElement(root, "node", attrib={"id": and_node_id, "label": "AND"})
            nodes[and_node_id] = and_node
            
            for reactant in reactants:
                if reactant not in nodes:
                    node = ET.SubElement(root, "node", attrib={"id": reactant, "label": reactant})
                    nodes[reactant] = node
                
                edge = ET.SubElement(root, "edge", attrib={"source": reactant, "target": and_node_id})
            
            for product in products:
                edge = ET.SubElement(root, "edge", attrib={"source": and_node_id, "target": product})
        else:
            for reactant in reactants:
                if reactant not in nodes:
                    node = ET.SubElement(root, "node", attrib={"id": reactant, "label": reactant})
                    nodes[reactant] = node
                
                for product in products:
                    edge = ET.SubElement(root, "edge", attrib={"source": reactant, "target": product})
        
        # Create inhibitor nodes and edges
        for inhibitor in inhibitors:
            if inhibitor not in nodes:
                node = ET.SubElement(root, "node", attrib={"id": inhibitor, "label": inhibitor})
                nodes[inhibitor] = node
            
            for product in products:
                edge = ET.SubElement(root, "edge", attrib={"source": inhibitor, "target": product, "label": "inhibits"})
    
    # Convert the XML tree to a string
    xgmml_string = ET.tostring(root).decode()
    
    # Save the XGMML output to a file
    if export_path:
        print(f"DEBUG/writeModel: export_path:{export_path}")
        filename = os.path.join(export_path, str(mymodel.modelName) + ".xgmml")
    else:
        filename = str(mymodel.modelName) + ".xgmml"
    print(f"DEBUG/model2xgmml: writing {filename}")
    
    with open(filename, "w") as f:
        f.write(xgmml_string)
        print(f"model2xgmml: written to {filename}")
        
# # TESTING                   
# mymodel = xls2model.createModel("exampleNet.xlsx")
# interaction_matrix_to_xgmml(mymodel, "test_network.xgmml")
