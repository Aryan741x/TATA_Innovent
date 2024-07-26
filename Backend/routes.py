from flask import Blueprint, jsonify, request
from app.camera import start_camera_traffic,stop_camera,start_camera_pothole,start_camera_both,list_available_cameras
from pymongo import MongoClient
import json
import os

routes = Blueprint('routes', __name__)

with open(os.path.join(os.path.dirname(__file__), 'traffic_signs_info.json')) as f:
    signs_data = json.load(f)

# Connect to MongoDB
try:
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client.traffic_signs
    collection = db.sign_info
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

#Camera Options
@routes.route('/cameras',methods=['GET'])
def send_options():
    available_cameras = list_available_cameras()
    return jsonify({'cameras': available_cameras})

#Start camera route
@routes.route('/start_camera', methods=['POST'])
def start_camera_route():
    camera_index = request.json.get('camera_index', 0)
    start_camera_traffic(camera_index)
    return jsonify({'message': 'Camera started'})

@routes.route('/start_camera_pothole', methods=['POST'])
def start_camera_pothole_route():
    camera_index = request.json.get('camera_index', 0)
    start_camera_pothole(camera_index)
    return jsonify({'message': 'Camera started'})

@routes.route('/start_camera_both', methods=['POST'])
def start_camera_both_route():
    camera_index = request.json.get('camera_index', 0)
    start_camera_both(camera_index)
    return jsonify({'message': 'Camera started'})



@routes.route('/stop_camera', methods=['POST'])
def stop_camera_route():
    stop_camera()
    return jsonify({'message': 'Camera stopped'})

@routes.route('/generate', methods=['POST'])
def generate_info():
    data = request.json
    signs = data['signs']
    sign_info_list = []

    if not signs:
        return jsonify({'error': 'Please provide a sign'}), 400

    for sign in signs:
        sign_info = collection.find_one({'sign': sign})
        if not sign_info:
            sign_info = signs_data.get(sign, {"details": "No details available", "action": "No action available"})
            collection.insert_one({'sign': sign, 'details': sign_info['details'], 'action': sign_info['action']})

        sign_info_list.append({'sign': sign, 'details': sign_info['details'], 'action': sign_info['action']})

    return jsonify(sign_info_list)

@routes.route('/signs', methods=['GET'])
def get_all_signs():
    try:
        signs = list(collection.find({}, {'_id': 0}))
        return jsonify(signs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500