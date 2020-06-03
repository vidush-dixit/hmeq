import numpy as np
from flask import Flask, request, jsonify, render_template
import pickle

app = Flask(__name__)
model = pickle.load(open('model.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyse', methods = ['POST'])
def analyse():
    # store form input in dictionary
    form_input = request.form.to_dict()
    
    # processing input data before feeding to Model
    # 1. Taking DEBTINC to last
    temp = form_input['DEBTINC']
    form_input.pop('DEBTINC', None)
    form_input['DEBTINC'] = temp

    # 2. Changing REASON to dummy column
    if form_input['REASON'] == 'HomeImp':
        form_input['HOMEIMP'] = 1
    else:
        form_input['HOMEIMP'] = 0
    # removing REASON
    form_input.pop('REASON', None)
    
    # 3. Changing JOB to value based on frequency ordering 
    job_dict = {'Other': 0, 'ProfExe': 1, 'Office': 2, 'Mgr': 3, 'Self': 4, 'Sales': 5}
    form_input['JOBIND'] = job_dict[form_input['JOB']]
    form_input.pop('JOB', None)

    # 4. Feature Scaling
    """from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaled_input = scaler.transform(processed_input)
    print(scaled_input)"""
    # 4. End Feature Scaling
    # End processing Data

    processed_input = [np.array([form_input[val] for val in form_input.keys()])]
    print(processed_input)
    temp_result = model.predict(processed_input)[0]
    print(temp_result)

    if(temp_result):
        result = 'BAD'
        return render_template('index.html', response_class = 'danger', response_title = 'Success',response_body = 'The Entered Loan Application looks {}'.format(result))
    else:
        result = 'GOOD'
        return render_template('index.html', response_class = 'success', response_title = 'Success',response_body = 'The Entered Loan Application looks {}'.format(result))

@app.route('/analyse_file', methods = ['POST'])
def analyse_file():
    data = request.get_json(force = True)
    prediction = model.predict([np.array(list(data.values()))])

    result = prediction[0]
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug = True)