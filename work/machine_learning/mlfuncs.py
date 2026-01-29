


def checkNull(df):
    import pandas as pd
    total = df.isnull().sum().sort_values(ascending = False)
    percent = (df.isnull().sum()/df.isnull().count()*100).sort_values(ascending = False)
    return pd.concat([total, percent], axis=1, keys=['Total_Null', 'Percent_Null']).transpose()



def colsToDateTime(df,date_cols):
    import pandas as pd
    for d in date_cols :
        df[d]= pd.to_datetime(df[d])
    return df



def objectToCategoryCols(df):
    for c in df.columns:
        col_type = df[c].dtype
        if col_type == 'object' or col_type.name == 'category':
            df[c] = df[c].astype('category')
    return df




def get_class_weights(y_train):
    # to address class imbalance during modelling process:
    from sklearn.utils import class_weight
    from sklearn.utils import compute_class_weight
    class_weights = compute_class_weight(class_weight = "balanced"
                                        ,classes = np.unique(y_train)
                                        ,y = y_train
                                        )

    class_weights = dict(zip(np.unique(y_train), class_weights))
    print(class_weights)
    return class_weights




def train_val_test_split(df,features,target):
    from sklearn.model_selection import train_test_split
    X_train, X_temp, y_train, y_temp= train_test_split(
                                                      df[features],
                                                      df.loc[:,target],
                                                      test_size = 0.3,
                                                      random_state = 1234,#random.randint(1,30),
                                                      stratify=df.loc[:,target]
                                                    )
    
    
    X_val, X_test, y_val, y_test= train_test_split(
                                                      X_temp,
                                                      y_temp,
                                                      test_size = 0.5,
                                                      random_state = 1234,#random.randint(1,30),
                                                      stratify=y_temp
                                                    )

    return X_train, X_val, X_test, y_train, y_val, y_test




def confusionMatrix(y_test,y_pred,str_modelname):
    import seaborn as sns
    import matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix
        
    title =  str_modelname
    label_list = sorted(list(set(list(y_test.unique())+ list(set(list(y_pred))))))
    
    cm = confusion_matrix(y_test,y_pred)
    fig, ax = plt.subplots(figsize=(8,5))
    ax = plt.subplot()
    sns.heatmap(cm, annot = True, fmt='g', ax=ax,#linewidths=.1,
                linecolor="Darkblue",cmap="Blues");
    fnt=13
    ax.set_xlabel('Predicted labels',fontsize=fnt);ax.set_ylabel('True labels',fontsize=fnt);
    ax.set_title(title,fontsize=fnt);
    ax.xaxis.set_ticklabels(label_list,fontsize=fnt)
    ax.yaxis.set_ticklabels(label_list,fontsize=fnt)
    
    #file= title+'.png'
    #plt.savefig(file,dpi=200, bbox_inches = 'tight')
    #return cm




def eda_categorical(df,categorical_cols,target,name):
    import pandas as pd
    import matplotlib.pyplot as plt
    
    for cat in categorical_cols:
        
        #freq chart
        pd.crosstab(df[cat],df[target]).plot(kind='bar')
        plt.title(name+' Frequency of '+ target)
        #plt.xlabel('Job')
        plt.ylabel('Frequency of '+ target)
        #plt.savefig('purchase_fre_job')

        #proportion chart
        table=pd.crosstab(df[cat],df[target])
        table.div(table.sum(1).astype(float), axis=0).plot(kind='bar', stacked=True)
        plt.title(name+' Stacked Bar Chart ' + target)
        #plt.xlabel(cat)
        plt.ylabel('Proportion of '+ target )
        #plt.savefig('mariral_vs_pur_stack')
        
        

        
def eda_qq_plots(df,numerical_cols):
    import numpy as np
    import statsmodels.api as sm
    import pylab as py
    for n in numerical_cols:
        print(n)
        sm.qqplot(df[n], line ='45')
        py.show()
        
      
    
    
    
def eda_histogram(df,target,numerical_cols,name):
    import pandas as pd
    import matplotlib.pyplot as plt
    for num in numerical_cols:
        fig, ax = plt.subplots(figsize=(11,5))
        ax.hist(df[(df[target]==1)][num], color='#007D00', alpha=0.7, label='1')
        ax.hist(df[(df[target]==0)][num], color='#8CB4E1', alpha=0.5,label='0')
        plt.xlabel(num, fontsize=12)
        plt.ylabel('frequency', fontsize=12)
        plt.title(name+num+' distribution by '+ target, fontsize=15)
        plt.tick_params(labelsize=12)
        plt.legend()
        plt.show()
        
        



      
def auc_logloss(y_test, y_pred_prob):
    print ('================= Model Evaluation: AUC & Logloss ==================================')
    from sklearn import metrics
    from sklearn.metrics import log_loss
    fpr, tpr, thresholds = metrics.roc_curve(y_test, y_pred_prob)
    auc = metrics.auc(fpr,tpr)
    logloss_score = log_loss(y_test, y_pred_prob)#, eps=1e-15)
    print ('AUC =', auc)
    print ('logloss =', logloss_score)
    return auc,logloss_score
    
    
    

    
def plot_roc_curve(modelname,y_test,y_pred_prob):
    from sklearn.metrics import roc_curve
    from sklearn.metrics import roc_auc_score

    my_auc = round(roc_auc_score(y_test,y_pred_prob),4)
    fpr1,tpr1,thresh1 = roc_curve(y_test,y_pred_prob,pos_label=1)
    random_probs = [0 for i in range(len(y_test))]
    p_fpr, p_tpr, _ = roc_curve(y_test, random_probs, pos_label=1)


    # matplotlib
    import matplotlib.pyplot as plt
    #plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(8,5))
    # plot roc curves
    plt.plot(fpr1, tpr1, linewidth=4,linestyle='--',color='black', label= modelname +' (AUC:'+str(my_auc)+')')
    plt.plot(p_fpr, p_tpr, linewidth=2,linestyle='--', color='grey')
    # title
    plt.title('ROC curve',fontsize=16)
    # x label
    plt.xlabel('False Positive Rate',fontsize=16)
    # y label
    plt.ylabel('True Positive rate',fontsize=16)

    plt.legend(loc='best')
    #plt.savefig('ROC',dpi=300)
    plt.show();



def confMatrix_ByThresholds(y_test,y_pred_prob,pos_class,neg_class):
    from sklearn.metrics import confusion_matrix, classification_report
    import numpy as np
    import pandas as pd
    #from pycm import ConfusionMatrix
    
    start =  0.015
    stop = 0.95
    step = 0.005
    myrange = np.arange(start,stop,step)
    
    evaluate = {'Threshold':[],
               'TruePosRate':[],
               'TrueNegRate':[],
               'Precision(PPV)':[],
               'NegPred(NPV)':[],
               'FalsePosRate':[],
               'FalseNegRate':[],
               'Accuracy':[]
               }
    
    
    evaluate_df = pd.DataFrame(evaluate)
    
    for i in myrange:
        import warnings
        warnings.filterwarnings(action='ignore',category=UserWarning)
        i=round(i,3)
        tmp_pred = np.where(y_pred_prob>i,pos_class,neg_class)
        cm =  confusion_matrix(y_test,tmp_pred)
        #print(cm)
        cm_pd = pd.crosstab(y_test,tmp_pred,rownames=['True'],colnames=['Predicted'],margins=True)
        #print(cm_pd)
        
        FP = cm.sum(axis=0) - np.diag(cm)
        FN = cm.sum(axis=1) - np.diag(cm)
        TP = np.diag(cm)
        TN = cm.sum() - (FP+FN+TP)
        
        FP = FP.astype(float)
        FN = FN.astype(float)
        TP = TP.astype(float)
        TN = TN.astype(float)
        
        #TRUE POSITIVE RATE ; RECALL
        TPR = TP/(TP+FN)
        # TRUE NEGATIVE RATE 
        TNR = TN/(TN+FP)
        
        #PRECISION
        PPV = TP/(TP+FP)
        #NEG PRED VALUE
        NPV = TN/(TN+FN)
        #FALSE POSTIVE RATE
        FPR = FP/(FP+TN)
        #FALSE NEG RATE
        FNR = FN/(TP+FN)
        #FALSE DISCOVERY RATE
        FDR = FP/(TP+FP)
        #ACCURACY
        ACC = (TP+TN)/(TP+FP+FN+TN)
        
        
        blank_df = {'Threshold':[i],
               'TruePosRate':[TPR[1]],
               'TrueNegRate':[TNR[1]],
               'Precision(PPV)':[PPV[1]],
               'NegPred(NPV)':[NPV[1]],
               'FalsePosRate':[FPR[1]],
               'FalseNegRate':[FNR[1]],
               'Accuracy':[ACC[1]]
                   }
        blank_df = pd.DataFrame(blank_df)
        #evaluate_df = evaluate_df.append(blank_df,ignore_index=True)
        evaluate_df = pd.concat([evaluate_df,blank_df],ignore_index=True)
    return evaluate_df




def minFalseNegRate(eval_df):
    metric = 'FalseNegRate'
    #cutoff = 0.5
    min_metric = min(eval_df[metric])
    threshold = round(eval_df[(eval_df[metric]==min_metric)].drop_duplicates(subset=[metric],keep='first').iloc[0]['Threshold'],3)
    #print(metric,min_metric,'\nprob cutoff:',threshold)
    eval_df_dedup = eval_df[(eval_df[metric]<=min_metric)].drop_duplicates(subset=[metric],keep='first')
    print('threshold:',threshold,'\n min_metric:',min_metric)
    return threshold,eval_df_dedup,min_metric