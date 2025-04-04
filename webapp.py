# webapp.py: Netflux2 web app
# Jeff Saucerman 3/2025
# Last updated 3/29/2025 JS: functional with exampleNet
# Requires: flask, flask-session >=0.6, numpy, matplotlib, scipy, lorenz
# To run webapp.py in Spyder, just hit run, then open http:/127.0.0.1:5000
#
# Current issues:
# Some bugs with status field, parameter updates.
#
# To do:
# Need to test with more models and conditions.

from flask import Flask, render_template, request, jsonify, session, g, send_from_directory
from flask_session import Session # server-side sessions
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import io, os, base64
import xls2model, model2PythonODE, model2xgmml

app = Flask(__name__)
app.secret_key = 'NetfluxNetfluxNetflux'       # for session variables
app.config['SESSION_TYPE'] = 'filesystem'   # server-side sessions
app.config['SESSION_FILE_DIR'] = './flask_sessions'
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MODELS_FOLDER'] = './models'

Session(app)                                # server-side sessions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/openmodel', methods=['GET','POST'])
def openmodel():   
    print("Starting openmodel")    
    try:
        if request.method == 'POST':
            if 'filename' in request.form:  # Check if default_filename is in form data
                filename = request.form['filename']
                print(f"DEBUG:openmodel filename:{filename}")
                filepath = os.path.join(app.config['MODELS_FOLDER'], filename)
                #print(f"DEBUG:openmodel filepath:{filepath}")
            elif 'file' in request.files:  # Check if file is uploaded via file dialog
                file = request.files['file']
                if file.filename == '':
                    return jsonify({"status": "Error: No file selected"}), 400
                filename = file.filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                print(f"{filename} send to uploads folder")
            else:
                return jsonify({"status": "Error: No file uploaded"}), 400
    
        # Generate model and parameters
        print(f"DEBUG/openmodel: filepath:{filepath}")
        mymodel = xls2model.createModel(filepath)
        modelName = mymodel.modelName
        print(f"DEBUG/openmodel: mymodel: {mymodel}")
        ODEfuncText = model2PythonODE.generateODEfile(mymodel)
        #print(f"DEBUG/openmodel: ODEfuncText: {ODEfuncText}")
        session.clear()
        session['NetfluxModel'] = mymodel
        session['reactionParams'] = mymodel.reactionParams
        session['speciesParams'] = mymodel.speciesParams
        #print(f"DEBUG/openmodel: speciesParams:{mymodel.speciesParams}")
        #print(f"DEBUG/openmodel: reactionParams: {mymodel.reactionParams}")
        session['ODEfuncText'] = ODEfuncText
            
        speciesIDs = mymodel.speciesIDs.tolist()  
        reactionRules = mymodel.reactionRules.tolist()
        session['speciesIDs'] = speciesIDs
        session['reactionRules'] = reactionRules
        #print(f"DEBUG/openmodel: speciesIDs:{speciesIDs}")
        #print(f"DEBUG/openmodel: reactionRules: {reactionRules}")
        return jsonify({"status": f"Status: Model {modelName} opened", "variables": speciesIDs, "reactionRules": reactionRules})
    except Exception as e:
        print(f"DEBUG/openmodel: Exception: {e}")
        return jsonify({'status': f'Status: Error opening model: {str(e)}'}) 
    return jsonify({"status": "Error processing file"}), 500

@app.route('/downloadmodel', methods=['POST'])
def downloadmodel():
    try:
        print("starting downloadmodel")
        # Assuming you have the model stored in the session; DEBUG: add error handling
        mymodel = session.get('NetfluxModel',[])
        #print(f"DEBUG/downloadmodel: mymodel.modelName:{mymodel.modelName}")

        # Export the ODE, params, and run files to the upload folder
        upload_folder = app.config['UPLOAD_FOLDER']
        #print(f"DEBUG/downloadmodel: exporting model to export_path: {upload_folder}")
        model2PythonODE.writeModel(mymodel,export_path=upload_folder)    
        modelName = mymodel.modelName
        print(f"DEBUG/downloadmodel: modelName:{modelName}")
        filenames = [f"{modelName}_ODEs.py", f"{modelName}_run.py", f"{modelName}_params.py"]
        return jsonify({"status": f"Status: {modelName} downloading", "filenames": filenames})
        
    except Exception as e:
        return jsonify({'status': f'Status: Error downloading model: py: {str(e)}'})

@app.route('/downloadxgmml', methods=['POST'])
def downloadxgmml():
    try:
        print("starting downloadxgmml")
        # Assuming you have the model stored in the session; DEBUG: add error handling
        mymodel = session.get('NetfluxModel',[])
        modelName = mymodel.modelName
        upload_folder = app.config['UPLOAD_FOLDER']
        model2xgmml.interaction_matrix_to_xgmml(mymodel, export_path=upload_folder)
        #print(f"DEBUG/downloadxgmml: modelName:{modelName}")
        filename = f"{modelName}.xgmml"
        return jsonify({"status": f"Status: {modelName} XGMML downloading", "filename": filename})
        
    except Exception as e:
        return jsonify({'status': f'Status: Error downloading XGMML: {str(e)}'})

@app.route('/downloadSimulation', methods=['POST'])
def downloadSimulation():
    try:
        print("starting downloadSimulation")
        # Assuming you have the simulation stored in t and y; DEBUG: add error handling
        mymodel = session.get('NetfluxModel',[])
        modelName = mymodel.modelName
        speciesIDs = mymodel.speciesIDs.tolist()
        print(f"DEBUG/downloadSimulation: speciesIDs:{speciesIDs}")
        t = np.array(session.get('t', [])) # session variable
        y = np.array(session.get('y', [])).T # transpose so it matches shape of t
        
        if t.size == 0 or y.size == 0:
            raise ValueError("t or y arrays are empty")
        print(f"DEBUG/downloadSimulation: y: {y}")
        print(f"DEBUG/downloadSimulation: y.shape: {y.shape}")
        
        df = pd.DataFrame(t, columns=['t'])
        for i, species in enumerate(speciesIDs):
            df[species] = y[:, i]
        print(f"DEBUG/downloadSimulation: df: {df}")
        filename = f"{modelName}_simulation.csv"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        df.to_csv(filepath, index=False)
        # if os.path.exists(filepath):
        #     print(f"DataFrame successfully written to {filepath}")

        return jsonify({"status": f"Status: {filename} exported to uploads folder", "filename": filename})
        
    except Exception as e:
        return jsonify({'status': f'Status: Error downloading simulation: {str(e)}'})

@app.route('/uploads/<filename>')
def download_file(filename):
    print(f"DEBUG/download_file: serving /uploads/{filename}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/library')
def library():
    return render_template('library.html')

@app.route('/help')
def helppage():
    return render_template('help.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/simulate', methods=['POST'])
def simulate():     # runs when you hit Simulate button
    print("DEBUG/simulate: starting simulate()")
    try:
        data = request.get_json()
        tmax = float(data['tmax'])
        tspan = [0, tmax]
        #print(f"DEBUG/simulate: session vars: {list(session.keys())}") # confirm NetfluxModel, ODEfuncText, loadParamsText getting passed  
        ODEfuncText = session.get('ODEfuncText','ODEfuncText not found')
        speciesParams = np.array(session.get('speciesParams', []))
        reactionParams = np.array(session.get('reactionParams', []))
        y0, ymax, tau = speciesParams[:, 0], speciesParams[:, 1], speciesParams[:, 2]
        w, n, EC50 = reactionParams[:, 0], reactionParams[:, 1], reactionParams[:, 2]

        # load ODEfunc using Flask g variable
        local_namespace = {}
        global_namespace = {'np': np} 
        exec(ODEfuncText, global_namespace, local_namespace)
        global_namespace.update(local_namespace)
        g.ODEfunc = local_namespace['ODEfunc']     
        #print(f"DEBUG/simulate: simulating {g.ODEfunc}")

        # Either continue or run new simulation
        if 'y' in session: # continue simulation
            told = np.array(session.get('t', [])) # DE-JSONIFY session variable
            yold = np.array(session.get('y', []))
            y0 = yold[:,-1]
            tspan = tspan + told[-1] 
            solution = solve_ivp(g.ODEfunc, tspan, y0, rtol=1e-8, args=(ymax, tau, w, n, EC50))        
            t = np.hstack([told,solution.t])
            y = np.hstack([yold,solution.y])
        else:
            solution = solve_ivp(g.ODEfunc, tspan, y0, rtol=1e-8, args=(ymax, tau, w, n, EC50))     
            t = solution.t
            y = solution.y
        session['t'] = t.tolist() # make JSON compatible
        session['y'] = y.tolist()
        plot_url = create_plot()   
        print("DEBUG: finished simulate()") 
        return jsonify({'status': 'Status: Simulation complete', 'plot': plot_url}) 
    except Exception as e:
        print(f"DEBUG: simulate Exception: {e}")
        return jsonify({'status': f'Status: Error: {str(e)}'})
    
def create_plot():     # creates the plot
    #print("DEBUG: start create_plot()")  
    try:
        data = request.get_json()
        #print(f"DEBUG/create_plot: session vars: {list(session.keys())}") 
        #print(f"DEBUG/create_plot: data: {data}") # BUG: currently only contains tmax
        selectedVariables = data['selectedVariables'] # selected variables from multi-select
        t = np.array(session.get('t', [])) # session variable
        y = np.array(session.get('y', []))
        mymodel = session.get('NetfluxModel',[])
        plotVars = np.array([index for index, value in mymodel.speciesIDs.items() if value in selectedVariables]) - 1  # subtract bc dataseries starts at 1
        #print(f"DEBUG/create_plot: plotting selected variabes {plotVars} ")
        
        plt.figure()
        plt.plot(t,y[plotVars,:].T)
        plt.legend(selectedVariables)
        plt.xlabel('Time')
        plt.ylabel('Normalized activity')        
        img = io.BytesIO()
        plt.savefig(img, format='png')
        #plt.show() # DEBUG
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode('utf8')
        print("DEBUG: finished create_plot()")
        return plot_url
        
    except Exception as e:
        print("DEBUG: error in create_plot")
        return jsonify({'status': f'Status: Error in create_plot: {str(e)}'})
    
@app.route('/replot', methods=['POST'])
def replot():     # runs when you click Plot button
    print("DEBUG: starting replot()")
    try:
        plot_url = create_plot()
        return jsonify({'status': 'Status: Plot updated', 'plot': plot_url}) 
    except Exception as e:
        print(f"DEBUG: simulate Exception: {e}")
        return jsonify({'status': f'Status: Error: {str(e)}'})

@app.route('/resetparams', methods=['POST'])
def resetparams():  # runs when you click Reset Parameters
    print("DEBUG: starting resetparams()")
    mymodel = session.get('NetfluxModel',[])
    speciesIDs = mymodel.speciesIDs.tolist()
    reactionRules = mymodel.reactionRules.tolist()
    speciesParams = np.array(mymodel.speciesParams) 
    reactionParams = np.array(mymodel.reactionParams) 
    #print(f"DEBUG/resetparams: reaectionParams:{reactionParams}")
    y0, ymax, tau = speciesParams[:, 0].tolist(), speciesParams[:, 1].tolist(), speciesParams[:, 2].tolist()
    w, n, ec50 = reactionParams[:, 0].tolist(), reactionParams[:, 1].tolist(), reactionParams[:, 2].tolist()  
    session['y0'], session['ymax'], session['tau'] = y0, ymax, tau
    session['w'], session['n'], session['EC50'] = w, n, ec50
    session['speciesParams'] = speciesParams # overwrite current values with original values
    session['reactionParams'] = reactionParams
    #print(f"DEBUG: y0:{y0} ymax:{ymax} tau:{tau}")
    #print(f"DEBUG: w:{w} n:{n}, ec50:{ec50} ")    
    return jsonify({'status': 'Status: Parameters reset', 'speciesIDs':speciesIDs, \
                    'reactionRules':reactionRules, 'y0':y0, 'ymax':ymax, 'tau':tau, \
                    'w':w, 'n':n, 'ec50':ec50})

@app.route('/resetsim', methods=['POST'])
def resetsim():  # runs when you click Reset Simulation
    print("DEBUG: starting resetsim()")
    session.pop('t', None)
    session.pop('y', None)
    tmax = 10   # FIXME: hard code this or load it from the form?
    return jsonify({'status': 'Status: Simulation reset', 'tmax':tmax}) 

@app.route('/updateSpeciesParams', methods=['GET','POST'])
def updateSpeciesParams():  # when you change a parameter value, this saves it into speciesParams
    #print("DEBUG: starting updateSpeciesParams()")
    data = request.get_json()
    selectedSpecies, y0, ymax, tau = data['selectedSpecies'], float(data['y0']), float(data['ymax']), float(data['tau'])
    speciesIDs = session.get('speciesIDs',[])
    speciesParams = np.array(session.get('speciesParams',[]))
    #print(f"DEBUG/updateSpeciesParams: speciesParams: {speciesParams}")
    pos = speciesIDs.index(selectedSpecies)
    speciesParams[pos,0] = y0
    speciesParams[pos,1] = ymax
    speciesParams[pos,2] = tau
    session['speciesParams'] = speciesParams
    #print(f"DEBUG/updateSpeciesParams: updated species: {selectedSpecies}, y0: {y0}, ymax: {ymax}, tau: {tau}")
    print("DEBUG finished updateSpeciesParams()")
    return jsonify({'status': 'Status: Updated species parameters'})

@app.route('/updateReactionParams', methods=['GET','POST'])
def updateReactionParams(): # when you change a parameter value, this saves it into reactionParams
    #print("DEBUG: starting updateReactionParams()")
    data = request.get_json()
    selectedReaction, w, n, ec50 = data['selectedReaction'], float(data['w']), float(data['n']), float(data['ec50']), 
    reactionRules = session.get('reactionRules',[])
    reactionParams = np.array(session.get('reactionParams',[]))
    #print(f"DEBUG/updateReactionParams: reactionParams: {reactionParams}")
    pos = reactionRules.index(selectedReaction)
    reactionParams[pos,0] = w
    reactionParams[pos,1] = n
    reactionParams[pos,2] = ec50
    session['reactionParams'] = reactionParams
    #print(f"DEBUG/updateReactionParams: updated reaction: {selectedReaction}, w: {w}, n: {n}, ec50: {ec50}")
    #print("DEBUG: finished updateReactionParams()")
    return jsonify({'status': 'Status: Updated species parameters'})

@app.route('/getSelectedSpeciesParams', methods=['POST'])
def getSelectedSpeciesParams(): # when you change which parameter is selected, this reloads the parameter values into the fields
    #print("DEBUG: starting getSelectedSpeciesParams")
    data = request.get_json()
    selectedSpecies = data['selectedSpecies']
    speciesIDs = session.get('speciesIDs',[])
    speciesParams = np.array(session.get('speciesParams',[]))
    pos = speciesIDs.index(selectedSpecies)
    #print(f"DEBUG/getSelectedSpeciesParams: speciesParams: {speciesParams}")
    #print(f"DEBUG/getSelectedSpeciesParams: pos:{pos}")
    y0, ymax, tau = speciesParams[pos,0], speciesParams[pos,1], speciesParams[pos,2] 
    #print(f"DEBUG/getSelectedSpeciesParams y0:{y0}, ymax:{ymax}, tau:{tau}")
    return jsonify({'status': 'Status: Updated species parameters', 'y0':y0, 'ymax':ymax, 'tau':tau})

@app.route('/getSelectedReactionParams', methods=['POST'])
def getSelectedReactionParams(): # when you change which parameter is selected, this reloads the parameter values into the fields
    #print("DEBUG: starting getSelectedReactionParams")
    data = request.get_json()
    selectedReaction = data['selectedReaction']
    reactionRules = session.get('reactionRules',[])
    reactionParams = np.array(session.get('reactionParams',[]))
    pos = reactionRules.index(selectedReaction)
    #print(f"DEBUG/getSelectedReactionParams: reactionParams: {reactionParams}")
    #print(f"DEBUG/getSelectedReactionParams: pos:{pos}")
    w, n, ec50 = reactionParams[pos,0], reactionParams[pos,1], reactionParams[pos,2] 
    #print(f"DEBUG/getSelectedReactionParams w:{w}, n:{n}, ec50:{ec50}")
    return jsonify({'status': 'Status: Updated reaction parameters', 'w':w, 'n':n, 'ec50':ec50})

# So that it will run in Spyder
if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='127.0.0.1', port=5000, debug=False) # Spyder crashes with debug=True