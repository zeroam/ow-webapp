import json

from algorithm import obj_detection
from flask import Flask, jsonify, render_template, request
from rq import Queue
from rq.job import Job
from worker import conn

app = Flask(__name__)
app.config.from_object("config.DevelopmentConfig")

q = Queue(connection=conn)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/obj_detect", methods=["POST"])
def get_objs():
    data = json.loads(request.data.decode())
    url = data["url"]

    # start a job
    job = q.enqueue_call(func=obj_detection, args=(url,), result_ttl=5000)

    return job.get_id()


@app.route("/results/<job_key>", methods=["GET"])
def get_results(job_key):
    job = Job.fetch(job_key, connection=conn)

    if job.is_finished:
        result = job.result
        return jsonify(result)
    else:
        return "Processing...", 202


if __name__ == "__main__":
    app.run()
