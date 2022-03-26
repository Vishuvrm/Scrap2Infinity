# src = https://blog.miguelgrinberg.com/post/using-celery-with-flask

import os
import time

from flask import Flask, request, render_template, session, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import BYTEA
from flask_migrate import Migrate
# import mysql.connector
from celery import Celery
from .scraping_engine.main import fetch_image_urls, get_selenium
from .scraping_engine.save_imgs import persist_image
import zipfile
import shutil
from werkzeug.utils import secure_filename
import uuid as uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top-secret!'
app.config['UPLOAD_FOLDER'] = os.path.abspath(r"./Scrap2Infinity/static/uploads")

# Celery configuration
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379'
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@localhost/uploads"


# app.config['CELERY_BROKER_URL'] = os.environ["REDIS_URL"]
# # app.config['CELERY_RESULT_BACKEND'] = os.environ["REDIS_URL"]
# app.config["result_backend"] = os.environ["REDIS_URL"]
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["UPDATED_DATABASE_URL"]

app.config["ZIP-PATH"] = []
app.config["num_uploads"] = 0

app.config["tasks"] = []

# Initialize the database
db = SQLAlchemy(app)

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Create table models
class UploadData(db.Model):
    filename = db.Column(db.String(200), nullable=False, primary_key=True)
    data = db.Column(BYTEA())

# def create_db(host="localhost", user="root", passwd="passwd", db="uploads"):
#     mydb = mysql.connector.connect(host="localhost",
#                                    user="root",
#                                    passwd="")
#     cur = mydb.cursor()
#     cur.execute(f"""CREATE DATABASE IF NOT EXISTS {db}""")
#     cur.execute("SHOW DATABASES")
#     print("Create database users")

# create_db()
# Migrate the changes to the database
migrate = Migrate(app, db)


# Clearing the uploads regularly
# @celery.task(bind=True)
def clear_uploads():
    print("UPLOAD_FOLDER = ", app.config["UPLOAD_FOLDER"])
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        # if not file.endswith(".txt"):
        os.remove(os.path.join(os.path.abspath(app.config['UPLOAD_FOLDER']),file))
    print("Cleared all files!")

# Create an empty static folder if it doesn't exists
# @celery.task(bind=True)
def create_empty_static():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    return os.path.exists(app.config['UPLOAD_FOLDER'])

# create_empty_static.apply_async()

# clear_process = Process(target=clear_uploads, args=())


def zip_directory(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, mode='w') as zipf:
        len_dir_path = len(folder_path)
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, file_path[len_dir_path:])
                print("FILE PATH =", file_path)
        zipf.close()

def writeTofile(data, filename):
    # Convert binary data to proper format and write it on Hard Disk
    with open(filename, 'wb') as file:
        file.write(data)
    print("Stored blob data into: ", filename, "\n")

@celery.task(bind=True)
def handle_images(self, img, qty, image_name, location_to_save, full_path, zip_path):
    create_empty_static()
    total = 100
    # location_to_save = r"static/uploads"
    self.update_state(state="PROGRESS", meta={'current': 25, 'total': total, 'status': "Fetching images url"})

    urls = fetch_image_urls(img, qty, get_selenium(), 1)

    self.update_state(state="PROGRESS", meta={'current': 50, 'total': total, 'status': f"URLs for {qty} images fetched!"})

    self.update_state(state="PROGRESS", meta={'current': 75, 'total': total, 'status': f"Fetching images from the url to a temporary folder"})
    persist_image(location_to_save, urls, image_name)

    zip_directory(full_path, zip_path)
    shutil.rmtree(full_path)

    self.update_state(state="PROGRESS", meta={'current': 90, 'total': total,
                                              'status': f"Uploading the zip folder to the online database"})

    with open(zip_path, "rb") as file:
        data = file.read()
        file.close()
    upload = UploadData(filename=image_name, data=data)
    db.session.add(upload)
    db.session.commit()

    os.remove(zip_path)


    # full_path = os.path.join(location_to_save, image_name)
    # zip_path = f"{full_path}.zip"
    # app.config["ZIP-PATH"] = zip_path

    # self.update_state(state="PROGRESS", meta={'current': 90, 'total': total, 'status': f"Saving the images to {os.path.basename(zip_path)}"})
    # zip_directory(full_path, zip_path)
    # shutil.rmtree(full_path)

    print("ZIP-PATH =", zip_path)
    # delete_zip.apply_async([zip_path])
    # with open(f"{full_path}_x.zip", "rb") as file:
    #     file = FileStorage(file)
    #     file.save(zip_path)
    #     file.close()
    # size = os.path.getsize(zip_path)
    # os.remove(f"{full_path}_x.zip")
    #
    # file = dill.dumps(file, recurse=True)
    # dill.loads(file)

    meta={"current": 100, "filename": image_name, "zip_path": zip_path, "download_as": img, "total": total, "status": f"Zipped images ready to download!", "result": "The images will disappear after 10 minutes. Please download them now!"}

    return meta

@celery.task(bind=True)
def delete_zip(self, zip_path):
    time.sleep(15)
    os.remove(zip_path)
    print("Remove the zip path!")

@app.route('/', methods=['GET', 'POST'])
def index():
    signal = create_empty_static()
    clear_uploads()

    if request.method == 'GET':
        return render_template('index.html', signal = signal)
    return redirect(url_for('index'))


@app.route('/longtask', methods=['POST'])
def longtask():
    if request.method == "POST":
        # data = (request.form["data"])
        signal = create_empty_static()
        if app.config["num_uploads"] < 5:
            img = request.form["img"]
            sec_img_name = secure_filename(img)
            image_name = f"{uuid.uuid1()}_{sec_img_name}"

            location_to_save = app.config['UPLOAD_FOLDER']
            full_path = os.path.join(location_to_save, image_name)
            zip_path = f"{full_path}.zip"
            app.config["ZIP-PATH"].append(zip_path)

            qty = request.form["qty"]
            task = handle_images.apply_async([img, int(qty), image_name, location_to_save, full_path, zip_path]) # or long_task.delay()
            # meta = task.result
            # zip_content = meta["zip_content"]
            # zip_content.save(zip_path)
            # with open(zip_path, "wb") as file:
            #     file.write(zip_content)
            #     file.close()

            app.config["num_uploads"] += 1
            celery.conf.update(app.config)
            return jsonify({}), 202, {'Location': url_for('taskstatus',
                                                          task_id=task.id)}



@app.route('/status/<task_id>')
def taskstatus(task_id):
    task = handle_images.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'current': 0,
            'total': 1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response["result"] = task.info["result"]
            response["zip_path"] = task.info["zip_path"]
            response["download_as"] = task.info["download_as"]
            filename = task.info["filename"]
            upload = UploadData.query.filter_by(filename=filename).first()
            data = upload.data
            writeTofile(data, task.info["zip_path"])
            UploadData.query.filter_by(filename=filename).delete()
            db.session.commit()
            # zip_file = task.info["zip_file"][1:]
            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            # print(zip_file)
            # print("***************************************************************************************")
            # print(type(zip_file))
            # print(len(zip_file))
            # bytes_zip = zip_file.encode("utf-8")
            # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            # print(bytes_zip)
            # print("****************************************************************************************")
            # print(type(bytes_zip))
            # print(len(bytes_zip))
            # file = dill.loads(bytes_zip)
            # # file=dill.loads(ast.literal_eval(bytes_zip))
            # file = dill.loads(zip_file)
            # file.save(r"F:\WebScraping\Scrap2Infinity\static\uploads\demo.zip")
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

def remove_zip(zip_path):
    time.sleep(15)
    os.remove(zip_path)

# @app.route("/delete-zip/<string:zip_path>")
# @celery.task(bind=True)
# def delete(zip_path):
#     time.sleep(5)
#     p = Process(target=remove_zip, args=(zip_path,))
#     p.start()
#     print("Remove the zip path!")

@app.after_request
def delete(response):
    response.direct_passthrough = False
    response_value = response.get_data()

    try:
        decoded_response = response_value.decode('utf-16').replace(r'\n', '')
        response_type = eval(f"type({decoded_response})")
    except SyntaxError:
        response_type = str
    except UnicodeDecodeError:
        response_type = str
    if ((rb"<html>" in response_value) or (response_type == dict)):
        pass
    else:
        zip_path = app.config["ZIP-PATH"]
        print("ZIP-PATH =", zip_path)
        # delete_zip.apply_async([zip_path])
        # p = Process(target=remove_zip, args=(zip_path,))
        # p.start()
        # print("Removed the zip path!")


    return response

if __name__ == '__main__':
    app.run(debug=True)
