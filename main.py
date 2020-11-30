import os
import mysql.connector
from mysql.connector import Error
from app import app
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from authenticate import token_required
import datetime
import jwt
import json

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
SECRET_KEY = "hkBxrbZ9Td4QEwgRewV6gZSVH4q78vBia4GBYuqd09SsiMsIjH"

@app.route('/loginEndpoint', methods=['POST'])
def loginFunction():
    userName = request.form.get('username')
    userList = ["nguyenanh1", "nguyenanh2", "nguyenanh3"]
    #Generate token
    if userName in userList:
        timeLimit= datetime.datetime.utcnow() + datetime.timedelta(minutes=30) #set limit for user
        payload = {"user_id": userName,"exp":timeLimit}
        token = jwt.encode(payload,SECRET_KEY)
        return_data = {
            "error": "0",
            "message": "Successful",
            "token": token.decode("UTF-8"),
            "Elapse_time": f"{timeLimit}"
            }
        return app.response_class(response=json.dumps(return_data), mimetype='application/json')
    else:
        return_data = {
            "error": "1",
            "message": "authorize failed",
            }
        return app.response_class(response=json.dumps(return_data), mimetype='application/json')




def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    
#connecto db    
def connect_sql():
    mydb = mysql.connector.connect(host="localhost",user="root", passwd="", database="test")
    return mydb

#execute query
def execute_sql(sql):
    try:
        mydb = connect_sql()
        mycursor = mydb.cursor()
        mycursor.execute(*sql)
        return mycursor, mydb
    except Error as error:
        print (error)
    
    
#close connection
def close_connect(mycursor, mydb):
    mycursor.close()
    mydb.close()


# insert data and return last insert id    
def insert_data(filename, id = None):
    if id is None:
        sql = ("""INSERT INTO testapi (name) VALUES (%s)""", (filename,))
    else:
        sql = ("""INSERT INTO testapi (name, id) VALUES (%s,%s)""", (filename,id,))
    
    try:
        mycursor, mydb = execute_sql(sql)
        mydb.commit()
        id = mycursor.lastrowid
        
    except Error as error:
        print (error)
    
    finally:
        close_connect(mycursor, mydb)
        return id


#update name in database 
def update_data(id, filename):
    sql = ("""update testapi set name = %s where id = %s """, (filename, id,))
    result = 0
    try:
        mycursor, mydb = execute_sql(sql)
        mydb.commit()
        result = mycursor.rowcount
            
    except Error as error:
        print (error)
    
    finally:
        close_connect(mycursor, mydb)
        return True


#delete data with id
def delete_data(id):
    sql = ("""delete from testapi where id = %s""", (id,))
    try:
        mycursor, mydb = execute_sql(sql)
        mydb.commit()
    except Error as error:
        print (error)
    finally:
        close_connect(mycursor, mydb)
        return True


def check_file_exits(id):
    sql = ("""select id from testapi where id = %s""", (id,))
    result = ()
    try:
        mycursor, mydb = execute_sql(sql)
        result = mycursor.fetchall()
        
    except Error as error: 
        print(error)
        
    finally:
        close_connect(mycursor, mydb)
        if result:
            return True
        else:
            return False
       
       
# upload file

@app.route('/file-upload', methods=['GET','POST'])
@token_required
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            resp = jsonify({'message' : 'No file part in the request'})
            resp.status_code = 400
            return resp
        file = request.files['file']
        if file.filename == '':
            resp = jsonify({'message' : 'No file selected for uploading'})
            resp.status_code = 400
            return resp
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            #insert vao csdl va lay ve idfilename
            id = insert_data(filename)
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(id)))
            resp = jsonify({'message' : 'File successfully uploaded' , 'id' : id})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify({'message' : 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'})
            resp.status_code = 400
            return resp
            
    return '''
     <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''
    
    
@app.route('/file-edit/<id>', methods=['PUT'])
def edit_file(id):
    update_or_create = None
    if 'file' not in request.files:
        resp = jsonify({'message':'file not include'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if file.filename == '':
        resp = jsonify({'message' : 'No file selected for uploadin'})
        resp.status_code = 400
        return resp
    if id:
        result = check_file_exits(id)
        filename = secure_filename(file.filename)
        if result:
            result = update_data(id, filename)
            update_or_create = 1
        else:
            id = insert_data(filename, id)
        
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(id)))
        if update_or_create:
            resp = jsonify({'message' : 'updated', 'id' : id})
        else:
            resp = jsonify({'message' : 'created', 'id' : id})
        resp.status_code = 200
        return resp
    
    
@app.route("/delete/<id>", methods=["DELETE"])
def delete_file(id):
    if check_file_exits(id):
        os.remove(str(id))
        delete_data(id)
        resp = jsonify({'message' : 'deleted', 'id' : id})
        resp.status_code = 200
        return resp
    else:
        resp = jsonify({'message' : 'not found', 'id' : id})
        resp.status_code = 404
        return resp
    
    
    
if __name__ == "__main__":
    app.run()