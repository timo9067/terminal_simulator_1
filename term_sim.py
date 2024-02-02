from flask import Flask, request, jsonify, abort
import json
from datetime import datetime, timedelta
import os
import time


app = Flask(__name__)

allowed_ips = ['223.25.76.60', '20.212.169.230', '84.46.82.194']

running = False

log_file_for_processing = "STS_Moves_z0_Up.json"

move_log = None

first_request = True

def pre_process_json(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_dir, filename)

    with open(filename,"r", encoding="utf-8-sig") as file:
        move_log = json.load(file).get("MoveLog", {}).values()
    
    # convertimg TimeStamp from str to datetime obj
    for record in move_log:
        record["TimeStamp"] = datetime.strptime(record['TimeStamp'], '%Y/%m/%d %H:%M:%S.%f')
    
    # sorting data by TimeStamp
    sorted_move_log = sorted(move_log, key=lambda x: x["TimeStamp"])

    
    # adding seconds for sending response into dictionary
    first_second = None
    first_timestamp = None
    
    for record in sorted_move_log:
        if not first_second and not first_timestamp:
            first_second = timedelta(seconds=1)
            first_timestamp = record["TimeStamp"]
            previous_sending_second = timedelta(seconds=0)

        sending_second = first_second + record["TimeStamp"] - first_timestamp

        if (sending_second - previous_sending_second) < timedelta(seconds=1):
            sending_second += timedelta(seconds=1)
        
        previous_sending_second = sending_second
    
        sending_second = int(sending_second.total_seconds())
        record.update({"SendingSecond": sending_second})
    
    return sorted_move_log

def process_record(start_time, request_time):
    global move_log
    
    elapsed_time = int(request_time - start_time)
    
    if move_log and (move_log[0]["SendingSecond"] <= elapsed_time):
        data = move_log.pop(0)

        timestamp = datetime.fromtimestamp(int(start_time+data["SendingSecond"]))

        del data["SendingSecond"]

        data["TimeStamp"] = timestamp.strftime('%Y/%m/%d %H:%M:%S.%f')
    else:
        data = {}
    return data

@app.before_request
def limit_remote_addr():
    flask_env = os.environ.get("FLASK_ENV", "development")
    if flask_env == "production" and (request.remote_addr not in allowed_ips):
        abort(403)

@app.route("/", methods=["GET"])
def main():
    global running
    global stop_event

    if running:
        message = r"Running. To get new response input /get-data, /start - to re-start process, /stop - to stop process"
    else: 
        message =  r"Ready to work. /start - to start process, /stop - to stop process, /get-data - to get current record"
    return jsonify({"Message": message})

@app.route("/start", methods=["GET"])
def start():
    global running
    global move_log
    global log_file_for_processing
    global first_request

    move_log = pre_process_json(log_file_for_processing)
    running = True
    first_request = True

    return jsonify({"Message": f"App is started. To get response enter /get-data"})

@app.route("/stop", methods=["GET"])
def stop():
    global running
    global move_log
    global first_request

    running = False
    move_log = None
    first_request = True

    return jsonify({"Message": "Process stopped. To run again enter /start"})

@app.route("/get-data", methods = ["GET"])
def get_data():
    global running
    global first_request
    global start_time

    if running:
        request_time = time.time()

        if first_request: 
            start_time = request_time
            first_request = False

        data = process_record(start_time, request_time)
        
        if not data and move_log:
            message = "Processing. No data available"
        elif not move_log:
            message = "All data is processed. To start processing again enter /start"
        else:
            message = "Processing. Data avilable"
            
    else:
        message = "To start processing data enter /start"
        data = {}


    return jsonify({"Message": message, "Data": data})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)