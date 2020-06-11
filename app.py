# ======================================= Importing Libraries ======================================
import pickle
import numpy as np
import pandas as pd

from io import BytesIO,StringIO
import zipfile

from flask import Flask, request, jsonify, redirect, url_for, render_template, send_file, make_response
from werkzeug.utils import secure_filename
#======================================= End Import Libraries ======================================

#======================================= App & Configurations ======================================
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
#===================================== End App & Configurations ====================================

#================================== Reading Trained Model File =====================================
model = pickle.load(open('model.pkl', 'rb'))
#================================== End Reading Trained Model File =================================

#===================================== User Defined Functions ======================================
ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
   return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preProcessData(input_dataframe):
    # allowed columns
    column_names = ['LOAN', 'MORTDUE', 'VALUE', 'REASON', 'JOB', 'YOJ', 'DEROG', 'DELINQ', 'CLAGE', 'NINQ', 'CLNO', 'DEBTINC']
    # creating temporary dataframe with allowed columns for processing
    modified_dataframe = input_dataframe[column_names].copy()
    
    # Creating Dummies for REASON and Dropping REASON and not keeping DEBTCON
    modified_dataframe['HOMEIMP'] = [ 1 if i == 'HomeImp' else 0 for i in modified_dataframe["REASON"] ]
    modified_dataframe.drop( ['REASON'], axis=1, inplace=True )
    
    # Assigning JOB categories values according to their frequencies
    job_frequency_dict = { 'Other': 0, 'ProfExe': 1, 'Office': 2, 'Mgr': 3, 'Self': 4, 'Sales': 5 }
    modified_dataframe['JOBIND'] = [ job_frequency_dict[i] for i in modified_dataframe['JOB'] ]
    modified_dataframe.drop( 'JOB', axis=1, inplace=True )

    return modified_dataframe

def download_files(uploaded_files_df):
    # if multiple files are there, zip and return files
    if len(uploaded_files_df) > 1:
        b_buffer = BytesIO()
        with zipfile.ZipFile(b_buffer, 'w') as zip:
            for fName, dataframe in uploaded_files_df.items():
                zip.writestr("{}".format(fName), dataframe.to_csv(index=False))
        zip.close()
        b_buffer.seek(0)
        
        response = make_response(b_buffer.getvalue())
        cd_headers = 'attachment; filename=csv-multiple.zip'
        response.headers['Content-Disposition'] = cd_headers
        response.mimetype = 'zip'

        return response
        # return send_file(b_buffer, mimetype='zip', attachment_filename='csv-multiple.zip', as_attachment=True)
    # if single file is there, return csv file only
    else:
        filename = ""
        s_buffer = StringIO()
        for fName, dataframe in uploaded_files_df.items():
            dataframe.to_csv(s_buffer, index=False)
            filename = fName
        filename = filename.rsplit('.', 1)[0]+'-new.csv'
        
        b_buffer = BytesIO()
        b_buffer.write(s_buffer.getvalue().encode('utf-8'))
        b_buffer.seek(0)
        s_buffer.close()

        response = make_response(b_buffer.getvalue())
        cd_headers = 'attachment; filename={}'.format(filename)
        response.headers['Content-Disposition'] = cd_headers
        response.mimetype='text/csv'

        return response
        # return send_file(b_buffer, mimetype='text/csv', attachment_filename=filename, as_attachment=True)

#=================================== End User Defined Functions ====================================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyse', methods = ['POST'])
def analyse():
    # store form input in dictionary
    form_input = request.form.to_dict()
    
    # moving DEBTINC column to last
    temp = form_input['DEBTINC']
    form_input.pop('DEBTINC', None)
    form_input['DEBTINC'] = temp

    # converting form input dictionary to dataframe & calling function for preprocessing
    dataframe_for_prediction = preProcessData( pd.DataFrame.from_dict( [form_input] ) )
    # converting processed dataframe to np-array to feed it to model for prediction
    processed_input = dataframe_for_prediction.iloc[:,:].values
    temp_result = model.predict(processed_input)[0]

    if(temp_result):
        result = 'BAD'
        return jsonify( status = 'success', result = result, resType = 'warning' )
    else:
        result = 'GOOD'
        return jsonify( status = 'success', result = result, resType = 'success' )

@app.route('/analyse_file', methods = ['POST'])
def analyse_file():
    # list of uploaded csv files in the form of file objects
    uploaded_files = request.files.getlist("files[]")
    # dictionary for filename : file->processed_dataframe
    uploaded_files_df = dict()

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            # getting secure filename so that it won't clash with any system config file
            uploaded_filename = secure_filename(file.filename)
            
            # converting csv file to dataframe
            uploaded_csv_file = pd.read_csv(file)
            # dropping rows with empty (NaN) values
            uploaded_csv_file = uploaded_csv_file.dropna().reset_index( drop=True )
            # uploaded_csv_file = uploaded_csv_file

            # converting processed dataframe to np-array to feed it to model for prediction
            processed_input = preProcessData(uploaded_csv_file).iloc[:,:].values
            temp_result = model.predict(processed_input)

            # creating prediction column in original dataframe
            uploaded_csv_file['Prediction'] = [ 'GOOD' if i == 0 else 'BAD' for i in temp_result ]
            
            # saving dataframe with predicted result to a dictionary for sending downloadable files
            uploaded_files_df[uploaded_filename] = uploaded_csv_file
        else:
            return jsonify( success = False, error = "Only CSV Allowed!!" )

    return download_files(uploaded_files_df)

if __name__ == "__main__":
    app.run(debug = True)