# webapp.py: Netflux2 web app
# Jeff Saucerman 3/2025
# Last updated 3/23/2025 JS: functional with exampleNet
# Requires: flask, flask-session >=0.6, numpy, matplotlib, scipy, lorenz
# To run webapp.py in Spyder, just hit run, then open http:/127.0.0.1:5000
#
# Current issues:
# Some bugs with status field.
# 3/25 fixed bugs with parameter order
#
# To do:
# Need to test with more models and conditions.

from flask import Flask, render_template, request, jsonify, session, g
from flask_session import Session # server-side sessions
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import io, os, base64
import xls2model, model2PythonODE

os.chdir('./myapp')
app = Flask(__name__)
app.secret_key = 'NetfluxNetfluxNetflux'       # for session variables
app.config['SESSION_TYPE'] = 'filesystem'   # server-side sessions
app.config['SESSION_FILE_DIR'] = './flask_sessions'
app.config['UPLOAD_FOLDER'] = './uploads'

Session(app)                                # server-side sessions

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/openmodel', methods=['GET','POST'])
def openmodel():
    # Opens file dialog, uploads Netflux xlsx, creates NetfluxModel with loadParams and ODEfunc attributes
    if 'file' not in request.files:
        return jsonify({"status": "Error: No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "Error: No file selected"}), 400

    if file:
        try:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            #filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename)) # BUGFIX JS 3/25 use absolute path instead of relative path
            file.save(filepath)
            print(f"{filename} uploaded")
    
            # Generate model and parameters
            mymodel = xls2model.createModel(filepath)
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
            return jsonify({"status": "Status: Model opened", "variables": speciesIDs, "reactionRules": reactionRules})
        except Exception as e:
            print(f"DEBUG/openmodel: Exception: {e}")
            return jsonify({'status': f'Status: Error opening model: {str(e)}'})
    
    return jsonify({"status": "Error processing file"}), 500

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
        #print("fDEBUG/simulate: parameters loaded")

        # load ODEfunc using Flask g variable
        local_namespace = {}
        global_namespace = {'np': np} 
        exec(ODEfuncText, global_namespace, local_namespace)
        global_namespace.update(local_namespace)
        g.ODEfunc = local_namespace['ODEfunc']     
        print(f"DEBUG/simulate: simulating {g.ODEfunc}")

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
    print(f"DEBUG/updateReactionParams: updated reaction: {selectedReaction}, w: {w}, n: {n}, ec50: {ec50}")
    print("DEBUG: finished updateReactionParams()")
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
    app.run(host='127.0.0.1', port=5000, debug=False) # Spyder crashes with debug=True