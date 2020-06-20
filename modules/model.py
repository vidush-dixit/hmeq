import pandas as pd
import numpy as np

def model_init():
    print('Initializing Model...')
    extVars_data = []

    main_df = pd.read_csv('./dataset/hmeq.csv')

    #=============== 1. Missing Data ===================
    #replacing with mean values
    mean_columns = ["MORTDUE","VALUE","DEBTINC","CLAGE"]
    mean_dict = dict()
    for i in mean_columns:
        #finding mean and replacing
        original_mean = main_df[i].mean()
        main_df[i] = main_df[i].fillna(original_mean)
        mean_dict[i] = original_mean
    extVars_data.append( mean_dict )

    #replacing with median values
    median_columns = ["YOJ","CLNO","NINQ"]
    median_dict = dict()
    for i in median_columns:
        #finding median and replacing
        original_median = main_df[i].median()
        main_df[i] = main_df[i].fillna(original_median)
        median_dict[i] = original_median
    extVars_data.append( median_dict )

    #replacing with mode values
    from statistics import mode
    mode_columns = ["REASON","JOB","DEROG","DELINQ"]
    mode_dict = dict()
    for i in mode_columns:
        #finding mean and replacing
        original_mode = mode(main_df[i])
        main_df[i] = main_df[i].fillna(original_mode)
        mode_dict[i] = original_mode
    extVars_data.append( mode_dict )
    #=========== 1. Missing values End ==============

    #================= 2. Outliers ==================
    data_numeric = main_df.select_dtypes(include=[np.number]).columns.values
    low = 0.005
    high = 0.995
    for col in data_numeric:
        if col not in ['BAD']:
            main_df[col] = np.where(main_df[col] < main_df[col].quantile(low), main_df[col].quantile(low),main_df[col])
            main_df[col] = np.where(main_df[col] > main_df[col].quantile(high), main_df[col].quantile(high),main_df[col])
    #================ 2. Outliers End ===============

    #============== 3. Categorical Data =============
    # Dummy for Reason Column
    main_df['HOMEIMP'] = [1 if i == 'HomeImp' else 0 for i in main_df["REASON"]]
    main_df.drop(['REASON'], axis=1, inplace=True)

    # dictionary based on frequency (by default in sorted order)
    job_frequency_dict = main_df['JOB'].value_counts().to_dict()
    print(job_frequency_dict)
    # Now replacing dictionary sorted frequencies with (0, 5)
    counter = 0
    for i in job_frequency_dict:
        job_frequency_dict[i] = counter
        counter += 1
    # creating JOBIND with sorted values of JOB column
    main_df['JOBIND'] = [job_frequency_dict[i] for i in main_df['JOB']]
    main_df.drop(['JOB'], axis = 1, inplace = True)
    #============ 3. Categorical End ================

    #============= 4. Feature Scaling ===============
    # from sklearn.preprocessing import StandardScaler
    # scaler = StandardScaler()
    # scaled_data = scaler.fit_transform(data.iloc[:,1:])
    # print(scaled_data)
    #=========== 4. End Feature Scaling =============

    # print(main_df.columns)

    #====== 5. Dependent and Independent Split ======
    y = main_df.iloc[:,0]
    x = main_df.iloc[:,1:]
    #==== 5. Dependent and Independent Split End ====

    #============= 6. Train Test Split ==============
    from sklearn.model_selection import train_test_split 
    xtrain, xtest, ytrain, ytest = train_test_split( x, y, test_size = 0.25, random_state = 0) 
    #============ 6. Train Test Split End ===========

    #============== 7. Model Training ===============
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score
    model = RandomForestClassifier(criterion='gini', max_depth=75, n_estimators=125, n_jobs=-1, warm_start=True)
    model.fit(xtrain, ytrain.ravel())
    extVars_data.append( model )
    #============= 7. Model Training End =============

    #============= 8. Saving trained Model ===========
    import pickle
    with open( "./extVars.pkl", "wb" ) as f:
        pickle.dump( extVars_data, f )
    #========== 8. End Saving Trained Model ==========

    #============= 9. Accuracy check =================
    y_pred = model.predict(xtest)
    accu_score = accuracy_score(ytest, y_pred)
    print('Accuracy: ', (accu_score*100).round(5),'%')
    #=========== 9. End Accuracy check ===============

    print('Model initialization successfully...')