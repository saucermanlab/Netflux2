# webapp.py for Netflux2 web app
# Jeff Saucerman 3/2025
# 3/15/2025 JS: adapted from Lorenz web app
# Current issues:
# none!
#
# To do:
# Fixing simulate()
# Status: 
#DEBUG: getting simulate Exception: name 'np' is not defined after loadParams

# Requires: flask, flask-session >=0.6, numpy, matplotlib, scipy, lorenz
# To run webapp.py in Spyder, just hit run, then open http:/127.0.0.1:5000

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, g
from flask_session import Session # server-side sessions
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
import io, os, base64, pickle
import lorenz # ODE function and parameters for Lorenz equations
import xls2model, model2PythonODE

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
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print(f"{filename} uploaded")

        # Generate model and parameters
        mymodel = xls2model.createModel(filepath)
        ODEfuncText = model2PythonODE.generateODEfile(mymodel)
        session.clear()
        session['NetfluxModel'] = mymodel
        session['reactionParams'] = mymodel.reactionParams
        session['speciesParams'] = mymodel.speciesParams
        session['ODEfuncText'] = ODEfuncText
        speciesIDs = mymodel.speciesIDs.tolist()  
        reactionRules = mymodel.reactionRules.tolist()
        #print(f"DEBUG/openmodel: speciesIDs:{speciesIDs}")
        #print(f"DEBUG/openmodel: reactionRules: {reactionRules}")
        return jsonify({"status": "Status: Model opened", "variables": speciesIDs, "reactionRules": reactionRules})
    
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
        print(f"DEBUG/simulate: session vars: {list(session.keys())}") # confirm NetfluxModel, ODEfuncText, loadParamsText getting passed  
        mymodel = session.get('NetfluxModel','Model not found') 
        ODEfuncText = session.get('ODEfuncText','ODEfuncText not found')
                
        # get species and reaction parameters from mymodel
        speciesParams = np.array(session.get('speciesParams', []))
        reactionParams = np.array(session.get('reactionParams', []))
        y0, ymax, tau = speciesParams[:, 0], speciesParams[:, 1], speciesParams[:, 2]
        w, n, EC50 = reactionParams[:, 0], reactionParams[:, 1], reactionParams[:, 2]
        print("DEBUG: paramters loaded")

        # load ODEfunc using Flask g variable
        local_namespace = {}
        global_namespace = {'np': np} 
        exec(ODEfuncText, global_namespace, local_namespace)
        global_namespace.update(local_namespace)
        g.ODEfunc = local_namespace['ODEfunc']     
        print(f"DEBUG/simulate: simulating {g.ODEfunc}")

        # Either continue or run new simulation
        if 'y' in session:
            told = np.array(session.get('t', [])) # DE-JSONIFY session variable
            yold = np.array(session.get('y', []))
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
    print("DEBUG: start create_plot()")  
    try:
        data = request.get_json()
        #print(f"DEBUG/create_plot: session vars: {list(session.keys())}") 
        #print(f"DEBUG/create_plot: data: {data}") # BUG: currently only contains tmax
        selectedVariables = data['selectedVariables'] # selected variables from multi-select
        t = np.array(session.get('t', [])) # session variable
        y = np.array(session.get('y', []))
        model = session.get('NetfluxModel',[])
        plotVars = np.array([index for index, value in model.speciesIDs.items() if value in selectedVariables]) - 1  # subtract bc dataseries starts at 1
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
        #print(f"DEBUG: simulate Exception: {e}")
        return jsonify({'status': f'Status: Error: {str(e)}'})

@app.route('/resetparams', methods=['POST'])
def resetparams():  # runs when you click Reset Parameters
    print("DEBUG: starting resetparams()")
    model = session.get('NetfluxModel')
    speciesIDs = model.speciesIDs.tolist()
    reactionRules = model.reactionRules.tolist()
    #print(f"DEBUG/resetparams: {speciesIDs}")
    speciesParams = np.array(model.speciesParams)
    reactionParams = np.array(model.reactionParams)
    y0, ymax, tau = speciesParams[:, 0].tolist(), speciesParams[:, 1].tolist(), speciesParams[:, 2].tolist()
    w, ec50, n = reactionParams[:, 0].tolist(), reactionParams[:, 1].tolist(), reactionParams[:, 2].tolist()  
    session['y0'], session['ymax'], session['tau'] = y0, ymax, tau
    session['w'], session['ec50'], session['n'] = w, ec50, n
    #print(f"DEBUG: y0:{y0} ymax:{ymax} tau:{tau}")
    #print(f"DEBUG: w:{w} ec50:{ec50} n:{n}")
    
    return jsonify({'status': 'Status: Parameters reset', 'speciesIDs':speciesIDs, \
                    'reactionRules':reactionRules, 'y0':y0, 'ymax':ymax, 'tau':tau, \
                    'w':w, 'ec50':ec50,'n':n})
# TODO: update index.html to update the parameter fields


@app.route('/resetsim', methods=['POST'])
def resetsim():  # runs when you click Reset Simulation
    print("DEBUG: starting resetsim()")
    session.pop('t', None)
    session.pop('y', None)
    tmax = 10   # FIXME: hard code this or load it from the form?
    return jsonify({'status': 'Status: Simulation reset', 'tmax':tmax}) 


# So that it will run in Spyder
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False) # Spyder crashes with debug=True