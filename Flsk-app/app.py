import requests
import os
import json
import csv
import boto3
import pandas as pd
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for

UPLOAD_FOLDER = './static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def hello_world():
    return render_template('home.html')

@app.route("/search", methods=['GET', 'POST'])
def search_food():
    error = None
    data = []
    if request.method == 'POST':
        input = request.form['input']
        url = 'https://yswql0o4gd.execute-api.us-east-1.amazonaws.com/test/helloworld?name='+input
        
        r = requests.get(url)

        data_json = r.json()

        if isinstance(data_json, list):
            data.extend(data_json)
        else:
            data.append(data_json)

        print(type(data))

        count=0
        for i in data:
            if i.get('fooditemname') != None and len(i.get('fooditemname')) > 0:
                count = count+1
                break
        if count == 0:
            data = []

    return render_template('results.html', data=data)


@app.route("/seach-ingredients", methods=['GET', 'POST'])
def searchIngredients():
    data=[]
    if request.method == 'POST':
        input = request.form['ingredients-list']
        input = input.replace(",","%7C")
        url = 'https://yswql0o4gd.execute-api.us-east-1.amazonaws.com/test/helloworld?ingredients='+input
        print(url)
        r = requests.get(url)
        data_json=r.json()

        if isinstance(data_json, list):
            data.extend(data_json)
        else:
            data.append(data_json)

        print(type(data))

        count=0
        for i in data:
            if i.get('fooditemname') != None and len(i.get('fooditemname')) > 0:
                count = count+1
                break
        if count == 0:
            data = []
    return render_template('results.html', data=data)

@app.route("/submit-recipie", methods=['GET', 'POST'])
def submitRecipie():
    error = None
    data=None
    if request.method == 'POST':
        dishName = request.form['dish-name']
        ingredients = request.form['ingredients']
        steps = request.form['steps']

        dishName = dishName.replace(",","%2C")
        ingredients = ingredients.replace(",","%2C")
        steps = steps.replace(",","%2C")

        url = 'https://yswql0o4gd.execute-api.us-east-1.amazonaws.com/test/helloworld?insert1='+dishName+'&insert2='+ingredients+'&insert3='+steps
        print(url)
        r = requests.get(url)
        print(r)
    return render_template('home.html')

@app.route("/search-image", methods=['GET', 'POST'])
def searchImage():
    error_image=None
    final_list = []
    names=[]
    if request.method == 'POST':
        # check if the post request has the file part
        if 'image' not in request.files:
            error_image='please select a file'
            return render_template('home.html', error_image = error_image)

        file = request.files['image']

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            error_image='No file selected'
            return render_template('home.html', error_image = error_image)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            error_image='Only allowed formats are .jpg, jpeg and .png'
            return render_template('home.html', error_image = error_image)

        ###############################################
        #access key
        with open('new_user_credentials-2.csv','r') as input:
            next(input)
            reader=csv.reader(input)
            for line in reader:
                access_key_id=line[2]
                secret_access_key=line[3]
        
        s3 = boto3.resource('s3',region_name='us-east-1',aws_access_key_id=access_key_id,aws_secret_access_key=secret_access_key)
        BUCKET = "food-recok-buck"

        photo = secure_filename(file.filename)
        print(file.filename)
        fp='static/uploads/'+photo

        s3.Bucket(BUCKET).upload_file(fp, photo)

        client = boto3.client('rekognition',region_name='us-east-1',aws_access_key_id=access_key_id,aws_secret_access_key=secret_access_key)

        response= client.detect_labels(Image={
         'S3Object': {
             'Bucket': 'food-recok-buck',
             'Name': photo
         }},MaxLabels=10,MinConfidence=95)

        jsonResp = json.dumps(response['Labels'],indent = 4)
        jsonResp = json.loads(jsonResp)

        ########################################
        for i in jsonResp:
            print(i['Name'])
            names.append(i['Name'])
            #searching for every output
            url = 'https://yswql0o4gd.execute-api.us-east-1.amazonaws.com/test/helloworld?name='+i['Name']
            r = requests.get(url)
            data = r.json()
            if isinstance(data, list):
                final_list.extend(data)
            else:
                final_list.append(data)
        count=0
        for i in final_list:
            if i.get('fooditemname') != None and len(i.get('fooditemname')) > 0:
                count = count+1
                break
        if count == 0:
            final_list = []

    return render_template('results.html', data=final_list, names = names)

if __name__ == "__main__":
    app.run( host='0.0.0.0', port=5000)