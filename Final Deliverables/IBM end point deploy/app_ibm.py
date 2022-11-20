
import pickle
import re
import sqlite3 as sql
import time
import ibm_db

import joblib
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas
import requests
from flask import Flask, render_template, request

API_KEY = "qJSD5ROm29i2iJGncQiHjCmDMgTx_563xkzVMRZ3Wvw3"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":
 API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=125f9f61-9715-46f9-9399-c8177b21803b.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud:31048;PORT=31498;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=wcq74792;PWD=NogApdfJJmMbemby",'','')
app = Flask(__name__)
model=pickle.load(open('rainfall.pkl','rb'))
scale=pickle.load(open('scale.pkl','rb'))
@app.route('/signin',methods =['GET', 'POST'])
def signin():
    global userid
    msg = ''
    if request.method == 'POST' :
        un = request.form['username']
        pd = request.form['password']
        sql = "SELECT * FROM register WHERE username =? AND password=?"
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,un)
        ibm_db.bind_param(stmt,2,pd)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print (account)
        if account:
            session['loggedin'] = True
            session['id'] = account['USERNAME']
            userid=  account['USERNAME']
            session['username'] = account['USERNAME']
            msg = 'Logged in successfully !'
            
            return render_template('dashboard.html', msg = msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('signin.html', msg = msg)
@app.route('/signup', methods=['POST','GET'])
def signup():
    msg=''
    if request.method == "POST":
        username=request.form['username']
        email=request.form['email']
        pw=request.form['password'] 
        sql='SELECT * FROM register WHERE email =?'
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt,1,email)
        ibm_db.execute(stmt)
        acnt=ibm_db.fetch_assoc(stmt)
        print(acnt)
            
        if acnt:
            msg='Account already exits!!'
            
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg='Please enter the avalid email address'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg='name must contain only character and number'
        else:
            insert_sql='INSERT INTO register VALUES (?,?,?)'
            pstmt=ibm_db.prepare(conn, insert_sql)
            ibm_db.bind_param(pstmt,1,username)
            ibm_db.bind_param(pstmt,2,email)
            ibm_db.bind_param(pstmt,3,pw)
            ibm_db.execute(pstmt)
            msg='You have successfully registered click signin!!'
            return render_template("signin.html")    

            
            
         
    elif request.method == 'POST':
        msg="fill out the form first!"
    return render_template("signup.html",msg=msg)
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/predict',methods=["POST","GET"])
def predict():
    input_feature=[x for x in request.form.values()]
    feature_values=[np.array(input_feature)]
    names=[['Location','MinTemp','MaxTemp','Rainfall','WindGustDir','WindGustSpeed','WindDir9am','WindDir3pm','WindSpeed9am','WindSpeed3pm','Humidity9am','Humidity3pm','Pressure9am','Pressure3pm','Cloud9am','Cloud3pm','Temp9am','Temp3pm','RainToday']]
    response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/cae560db-c5dc-4eba-b799-99e910c25da3/predictions?version=2022-11-04', json=names,
    headers={'Authorization': 'Bearer ' + mltoken})
    print("Scoring response")
    print(response_scoring.json())
    data=pandas.DataFrame(feature_values,columns=names)
    data=scale.fit_transform(data)
    data=pandas.DataFrame(data,columns=names)
    prediction =model.predict(data)
    pred_prob=model.predict_proba(data)
    print(prediction)
    if prediction == "Yes":
        return render_template("chance.html")
    else:
        return render_template("nochance.html")
if __name__ == "__main__": 
  app.run(debug=True)            