# ======================================= Importing Libraries ======================================
import pickle
import numpy as np
import random
from statistics import mode
import pandas as pd
import eli5

from io import BytesIO, StringIO
import zipfile
import base64

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from flask import Flask, request, jsonify, redirect, url_for, render_template, send_file, make_response
from werkzeug.utils import secure_filename
#======================================= End Import Libraries ======================================

#======================================= App & Configurations ======================================
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024
#===================================== End App & Configurations ====================================

#===================================== Reading Trained Model File ==================================
pckFile = open( 'extVars.pkl', 'rb' )
mean_dict, median_dict, mode_dict, model = pickle.load( pckFile )
pckFile.close()
#================================== End Reading Trained Model File =================================

#===================================== User Defined Functions ======================================
ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
   return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preProcessData(input_dataframe, newTraining_Data = False):
    # allowed columns
    column_names = ['LOAN', 'MORTDUE', 'VALUE', 'REASON', 'JOB', 'YOJ', 'DEROG', 'DELINQ', 'CLAGE', 'NINQ', 'CLNO', 'DEBTINC']
    # creating temporary dataframe with allowed columns for processing
    modified_dataframe = input_dataframe[column_names].copy()
    
    mean_columns = ["MORTDUE","VALUE","DEBTINC","CLAGE"]
    median_columns = ["YOJ","CLNO","NINQ"]
    mode_columns = ["REASON","JOB","DEROG","DELINQ"]

    if newTraining_Data == True:
        low = .005
        high = .995
        # 1. Imputing Missing Values
        # Replacing missing values with Mean, Median and Most Frequent Occupance (Mode)
        for col in modified_dataframe:
            if col in mean_columns:
                new_mean = ( modified_dataframe[col].mean() + mean_dict[col] ) / 2
                modified_dataframe[col].fillna( new_mean, inplace=True )
                mean_dict[col] = new_mean
            if col in median_columns:
                new_median = ( modified_dataframe[col].median() + median_dict[col] ) / 2
                modified_dataframe[col].fillna( new_median, inplace=True )
                median_dict[col] = new_median
            if col in mode_columns:
                if col not in [ 'REASON', 'JOB' ]:
                    new_mode = ( mode( modified_dataframe[col] ) + mode_dict[col] ) / 2
                else:
                    new_mode = random.choice( [ mode( modified_dataframe[col] ), mode_dict[col] ] )
                modified_dataframe[col].fillna( new_mode, inplace=True )
                mode_dict[col] = new_mode

        # 1. End Imputing Missing Values
        for col in modified_dataframe:
            # 1. Dealing with outliers
            if col not in [ 'REASON', 'JOB' ]:
                modified_dataframe[col] = np.where( modified_dataframe[col] < modified_dataframe[col].quantile(low), modified_dataframe[col].quantile(low), modified_dataframe[col] )
                modified_dataframe[col] = np.where( modified_dataframe[col] > modified_dataframe[col].quantile(high), modified_dataframe[col].quantile(high), modified_dataframe[col] )
            # 1. End Dealing with outliers
    else:
        # 1. Imputing Missing Values
        # Replacing missing values with Mean, Median and Most Frequent Occupance (Mode)
        for col in modified_dataframe:
            if col in mean_columns:
                modified_dataframe[col] = modified_dataframe[col].fillna( mean_dict[col] )
            if col in median_columns:
                modified_dataframe[col] = modified_dataframe[col].fillna( median_dict[col] )
            if col in mode_columns:
                modified_dataframe[col] = modified_dataframe[col].fillna( mode_dict[col] )
        # 1. End Imputing Missing Values
    
    # 2. Converting categorical Data
    # Creating Dummies for REASON and Dropping REASON and not keeping DEBTCON
    modified_dataframe['HOMEIMP'] = [ 1 if i == 'HomeImp' else 0 for i in modified_dataframe["REASON"] ]
    modified_dataframe.drop( ['REASON'], axis=1, inplace=True )
    
    # Assigning JOB categories values according to their frequencies
    job_frequency_dict = { 'Other': 0, 'ProfExe': 1, 'Office': 2, 'Mgr': 3, 'Self': 4, 'Sales': 5 }
    modified_dataframe['JOBIND'] = [ job_frequency_dict[i] for i in modified_dataframe['JOB'] ]
    modified_dataframe.drop( 'JOB', axis=1, inplace=True )
    # 2. End Converting Categorical Data

    return modified_dataframe

def download_files( uploaded_files_df, fileOption = 'removeMissing' ):
    # if multiple files are there, zip and return files
    if len(uploaded_files_df) > 1:
        b_buffer = BytesIO()
        with zipfile.ZipFile(b_buffer, 'w') as zip:
            for fName, dataframe in uploaded_files_df.items():
                zip.writestr(fName.rsplit('.', 1)[0]+'-new.csv', dataframe.to_csv(index=False))
        zip.close()
        b_buffer.seek(0)
        
        response = make_response(b_buffer.getvalue())
        cd_headers = 'attachment; filename=csv-multiple-'+ str(fileOption) +'.zip'
        response.headers['Content-Disposition'] = cd_headers
        response.mimetype = 'zip'
        b_buffer.close()

        return response
        # return send_file(b_buffer, mimetype='zip', attachment_filename='csv-multiple.zip', as_attachment=True)
    # if single file is there, return csv file only
    else:
        filename = ""
        s_buffer = StringIO()
        for fName, dataframe in uploaded_files_df.items():
            dataframe.to_csv(s_buffer, index=False)
            filename = fName.rsplit('.', 1)[0]+'-'+ str(fileOption) +'-new.csv'
        
        b_buffer = BytesIO()
        b_buffer.write(s_buffer.getvalue().encode('utf-8'))
        b_buffer.seek(0)
        s_buffer.close()

        response = make_response(b_buffer.getvalue())
        cd_headers = 'attachment; filename={}'.format(filename)
        response.headers['Content-Disposition'] = cd_headers
        response.mimetype='text/csv'
        b_buffer.close()

        return response
        # return send_file(b_buffer, mimetype='text/csv', attachment_filename=filename, as_attachment=True)

#=================================== End User Defined Functions ====================================

@app.route('/')
def home():
    df = pd.read_csv('hmeq.csv')
    df.dropna( inplace=True )
    df["BAD"] = ["BAD" if i == 1 else "GOOD" for i in df["BAD"]]
    df["CLTV"] = (df["LOAN"] +df["MORTDUE"]) / df["VALUE"]

    plt.figure( figsize = ( 12, 6 ) )
    annot_kws={
        'fontsize' : 20,
        'fontstyle' : 'oblique',
        'color' : "Black",
        'rotation' : "horizontal",
        'verticalalignment' : 'center',
        'backgroundcolor' : 'w'
        }

    sns.heatmap( pd.crosstab(df.BAD, df.REASON, values = df.CLTV, aggfunc = "mean"), annot = True, linewidths = 4, cmap = "YlGnBu", fmt = ".3f", annot_kws = annot_kws, cbar_kws = {'extend' : 'min'})

    plt.title( "Average CLTV", fontsize = 30, loc = 'center', 
                fontdict = { 'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 25})
    plt.xlabel( 'Reason for Loan',
                fontdict = { 'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 16})
    plt.ylabel( 'Status of Loan',
                fontdict = { 'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 16})

    plt.savefig("./static/img/Av_CLTV.png", bbox_inches='tight', pad_inches = 0)
    plt.close()

    plt.figure( figsize = (12,6) )
    annot_kws={
        'fontsize' : 20, 
        'fontstyle' : 'italic',  
        'color' : "Black",
        'rotation' : "horizontal",
        'verticalalignment' : 'center',
        'backgroundcolor' : 'w'
        }

    sns.heatmap(pd.crosstab(df.BAD, df.REASON, values = df.DEBTINC, aggfunc = "mean"), annot = True, linewidths = 4, cmap = "Wistia", fmt = ".3f", annot_kws = annot_kws, cbar_kws = {'extend' : 'min'})

    plt.title("Average Debt to income ratio", fontsize = 30, loc = 'center', 
            fontdict = { 'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 25 })
    plt.xlabel('Reason for Loan',
            fontdict = { 'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 16 })
    plt.ylabel('Status of Loan',
            fontdict = { 'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 16 })

    plt.savefig("./static/img/Av_DEBTINC.png", bbox_inches='tight', pad_inches = 0)
    plt.close()

    return render_template('index.html')

@app.route('/analyse', methods = ['POST'])
def analyse():
    try:
        # store form input in dictionary
        form_input = request.form.to_dict()
        form_input = { k: None if not v else v for k, v in form_input.items() }

        # moving DEBTINC column to last
        temp = form_input['DEBTINC']
        form_input.pop('DEBTINC', None)
        form_input['DEBTINC'] = temp

        int_columns = ['LOAN', 'YOJ', 'DEROG', 'DELINQ', 'NINQ', 'CLNO']
        float_columns = ['MORTDUE', 'VALUE', 'CLAGE', 'DEBTINC']
        
        # converting form input dictionary to dataframe & calling function for preprocessing
        dataframe_for_prediction = preProcessData( pd.DataFrame.from_dict( [form_input] ) )
        
        for i,v in dataframe_for_prediction.iloc[0].to_dict().items():
            if i not in ['HOMEIMP', 'JOBIND']:
                if i in int_columns:
                    form_input[i] = int(float(v))
                if i in float_columns:
                    form_input[i] = round(float(v),3)
            else:
                if i == 'HOMEIMP':
                    if v == 1:
                        form_input['REASON'] = 'HOMEIMP'
                    else:
                        form_input['REASON'] = 'DEBTCON'
                else:
                    job_frequency_dict = { 'Other': 0, 'ProfExe': 1, 'Office': 2, 'Mgr': 3, 'Self': 4, 'Sales': 5 }
                    form_input['JOB'] = list(job_frequency_dict.keys())[list(job_frequency_dict.values()).index(v)]
        
        # converting processed dataframe to np-array to feed it to model for prediction
        processed_input = dataframe_for_prediction.iloc[:,:].values
        temp_result = model.predict(processed_input)[0]

        explained_pred = eli5.explain_prediction_df(estimator=model, doc=dataframe_for_prediction.iloc[0])
        explained_pred = explained_pred[explained_pred.feature != '<BIAS>'].reset_index( drop=True )
        # print( explained_pred )
        explained_pred = explained_pred.iloc[:6]
        
        plt.figure( figsize = (12,6) )
        sns.barplot( x='weight', y='feature', data = explained_pred )
        plt.title("Top Features", fontsize = 30, loc = 'center', pad=10,
                fontdict = { 'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 25 })
        plt.xlabel('Importance',
                fontdict = { 'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 16 })
        plt.ylabel('Features',
                fontdict = { 'family': 'serif', 'color': 'darkred', 'weight': 'normal', 'size': 16 })
        plt.tick_params( labelsize=12 )
        
        img_buffer = BytesIO()
        plt.savefig( img_buffer, format='png', bbox_inches='tight', pad_inches = 0)
        plt.close()
        img_buffer.seek(0)
        plot_url = base64.b64encode( img_buffer.getvalue() ).decode('utf-8')

        if( temp_result == 0 ):
            category = 'GOOD'
            resType = 'success'
        else:
            category = 'BAD'
            resType = 'warning'
        
        features    = [ str(i) for i in form_input.keys() ] 
        values      = [ str(i) for i in form_input.values() ]
    except Exception as e:
        return jsonify( status='success', error = 'Something went wrong!! Contact Webmaster' )
    else:
        return jsonify( status='success', category=category, features=features, values=values, resType=resType, imgUrl=plot_url )

@app.route('/analyse_file', methods = ['POST'])
def analyse_file():
    missing_values_option = request.form.get( 'missingValuesOption' )
    # list of uploaded csv files in the form of file objects
    uploaded_files = request.files.getlist("files[]")
    # dictionary for {filename : file->processed_dataframe}
    uploaded_files_df = dict()

    for file in uploaded_files:
        if file and allowed_file(file.filename):
            # getting secure filename so that it won't clash with any system config file
            uploaded_filename = secure_filename(file.filename)
            # converting csv file to dataframe
            uploaded_csv_file = pd.read_csv(file)
            
            # Handling missing values
            # dropping rows with empty (NaN) values
            if missing_values_option == 'removeMissing':
                uploaded_csv_file = uploaded_csv_file.dropna().reset_index( drop=True )

            # converting processed dataframe to np-array to feed it to model for prediction
            processed_input = preProcessData( uploaded_csv_file )
            temp_result = model.predict( processed_input.iloc[:,:].values )

            # creating prediction column in original dataframe
            uploaded_csv_file['Prediction'] = [ 'GOOD' if i == 0 else 'BAD' for i in temp_result ]
            
            # saving dataframe with predicted result to a dictionary for sending downloadable files
            uploaded_files_df[uploaded_filename] = uploaded_csv_file
        else:
            return jsonify( success = False, error = "Only CSV Allowed!!" )

    return download_files( uploaded_files_df, missing_values_option )

@app.route('/upload_new_data', methods = ['POST'])
def retrain_model():
    # list of uploaded csv files in the form of file objects
    uploaded_csv_file = request.files.getlist("files[]")[0]

    if uploaded_csv_file and allowed_file( uploaded_csv_file.filename ):
        uploaded_csv_dataframe = pd.read_csv( uploaded_csv_file )
        
        Y = uploaded_csv_dataframe.loc[:, ['BAD']].values 
        # converting processed dataframe to np-array to feed it to model for prediction
        X = preProcessData( uploaded_csv_dataframe, True ).iloc[:,:].values

        try:
            model.n_estimators += 5
            model.fit( X, Y.ravel() )
        except Exception as e:
            return jsonify( success = False, error = 'Something went wrong! Try Again' )

        extVars_data = [ mean_dict, median_dict, mode_dict, model ]

        with open("extVars.pkl", "wb") as f:
            pickle.dump(extVars_data, f)
        return jsonify( success = True )

    return jsonify( success = False, error = 'Invalid File.' )

if __name__ == "__main__":
    app.run(debug = True)
