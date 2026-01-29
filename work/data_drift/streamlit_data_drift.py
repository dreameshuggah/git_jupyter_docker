#!/usr/bin/env python
# coding: utf-8

# In[2]:

# cd /Users/dreameshuggah/Documents/Rizal_Analytics/Data_Drift_Detection/
# streamlit run streamlit_data_drift.py 
import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import numpy as np

from pandasql import sqldf

from evidently.report import Report
from evidently.metrics import DataDriftTable
from evidently.metrics import DatasetDriftMetric

from evidently.test_suite import TestSuite
from evidently.test_preset import DataStabilityTestPreset





st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="auto", menu_items=None)

st.title('Data Drift Detection')



use_example_files = st.checkbox("Use example files"
                                , True
                                , help="Use in-built example files to demo the app"
                                )


st.text('\n')
reference_file = st.file_uploader("Upload Reference Data (csv)")#, accept_multiple_files=True)
st.text('\n')
current_file = st.file_uploader("Upload Current Data (csv)")#, accept_multiple_files=True)



if use_example_files:
  reference_file = 'small_ref_df.csv'
  reference_df = pd.read_csv(reference_file)#,usecols=['from','to'])
  
  current_file = 'small_cur_df.csv'
  current_df = pd.read_csv(current_file)#,usecols=['from','to'])
  

if reference_file and current_file:
  #@st.cache_data()
  reference_df = pd.read_csv(reference_file)#,usecols=['from','to'])
  current_df = pd.read_csv(current_file)#,usecols=['from','to'])




if reference_file and current_file and len(reference_df)> 0 and len(current_df)>0:
  st.text('\n')
  st.text('\n')
  st.text('\n')
  st.text('\n')
  st.text('Sample Reference Data')
  st.dataframe(reference_df[:5])
  st.text('Sample Current Data')
  st.dataframe(current_df[:5])


  cols = list(reference_df.columns)
  
  st.text('\n')
  st.text('\n')



if use_example_files:
  selected_cols = st.multiselect('Select Columns for Detection'
                                ,cols
                                ,['cc_num', 'merchant', 'category', 'amt']
                                )
                                
if use_example_files == False and reference_file and current_file:
  selected_cols = st.multiselect('Select Columns for Detection', cols)#,'rival')




# For instance checking orignal train data set X vs the validation data set X_val
data_drift_dataset_report = Report(metrics=[
                                          DatasetDriftMetric(),
                                          DataDriftTable(),    
                                          ])
                                          
                                          
                                          
                                          
if reference_file and current_file and selected_cols:
  data_drift_dataset_report.run(reference_data= reference_df[selected_cols]
                                ,current_data= current_df[selected_cols]
                                )
  
  fileName = "data_drift_dataset_report.html"
  data_drift_dataset_report.save_html(fileName)
  #net.save_graph(fileName)
  HtmlFile = open(fileName, 'r', encoding='utf-8')
  components.html(HtmlFile.read(), height=2000)
  #data_drift_dataset_report
