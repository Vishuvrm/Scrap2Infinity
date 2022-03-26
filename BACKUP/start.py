from Scrap2Infinity.app import app
from flask_apscheduler import APScheduler
#
# # initialize scheduler
scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)

@scheduler.task("interval", id="auto_uploads_clear",minutes=5, misfire_grace_time=None)
def auto_uploads_clear():
    for file in os.listdir(app.config['UPLOAD_FOLDER']):
        os.remove(os.path.join(os.path.abspath(app.config['UPLOAD_FOLDER']), file))
    print("Cleared all files!")

scheduler.start()


if __name__ == "__main__":
    print("app starting...")
    app.run(debug=True)