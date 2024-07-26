import os
from inference_sdk import InferenceHTTPClient
import argparse
import cv2 as cv
from app.socketio_instance import socketio
import numpy as np

camera_running = False
latest_result=None

CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=os.getenv("ROBOFLOW_API_KEY")
)

#Parse_arguments function is to set the correct resolution for the webcam
def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="YOLOv8 live")
    parser.add_argument(
        "--webcam-resolution", 
        default=[1280, 720], 
        nargs=2, 
        type=int
    )
    args = parser.parse_args()
    return args

def prediction_traffic(frame):
    result = CLIENT.infer(frame, model_id="indian-traffic-signboards-a0gtk/1")
    return result

def prediction_pothole(frame):
    result = CLIENT.infer(frame, model_id="pothole-detection-qnlw9/1")
    return result

def annotate_frame_traffic(frame, result):
    predictions = result.get('predictions', [])
    
    for pred in predictions:
        # Extract bounding box and label information
        x = pred['x']
        y = pred['y']
        width = pred['width']
        height = pred['height']
        confidence = pred['confidence']
        class_label = pred['class']
        
        # Calculate the top-left corner of the bounding box
        x1 = int(x - width / 2)
        y1 = int(y - height / 2)
        
        # Calculate the bottom-right corner of the bounding box
        x2 = int(x + width / 2)
        y2 = int(y + height / 2)
        
        # Draw the bounding box
        cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Create the label with class name and confidence
        label = f"{class_label} {confidence:.2f}"
        
        # Draw the label
        label_size, base_line = cv.getTextSize(label, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        y1 = max(y1, label_size[1])
        cv.rectangle(frame, (x1, y1 - label_size[1]), (x1 + label_size[0], y1 + base_line), (0, 255, 0), cv.FILLED)
        cv.putText(frame, label, (x1, y1), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    return frame

def annotate_frame_pothole(frame, result):
    # Extract predictions
    predictions = result.get('predictions', [])
    
    for pred in predictions:
        # Extract bounding box and label information
        confidence = pred['confidence']
        class_label = pred['class']
        
        # Extract points for the polygon
        points = pred['points']
        pts = np.array([[int(point['x']), int(point['y'])] for point in points], np.int32)
        pts = pts.reshape((-1, 1, 2))
        
        # Draw the polygon
        cv.polylines(frame, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
        
        # Calculate the position for the label
        x, y = pts[0][0]  # Use the first point for the label position
        label = f"{class_label} {confidence:.2f}"
        
        # Draw the label
        label_size, base_line = cv.getTextSize(label, cv.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        y = max(y, label_size[1])
        cv.rectangle(frame, (x, y - label_size[1]), (x + label_size[0], y + base_line), (0, 255, 0), cv.FILLED)
        cv.putText(frame, label, (x, y), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    return frame

def start_camera_traffic(camera_index):
    global camera_running, latest_result
    camera_running = True
    args=parse_arguments()
    cap = cv.VideoCapture(camera_index)

    #Setting the resolution of the webcam
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.webcam_resolution[0])
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.webcam_resolution[1])

    while camera_running:
        #Captures the frame
        ret, frame = cap.read()
        if not ret:
            break
        
        #Calls the prediction function
        latest_result = prediction_traffic(frame)
        frame = annotate_frame_traffic(frame, latest_result)

        socketio.emit('latest_result', {'result': latest_result})
        socketio.sleep(1)

        #Displays the frame in continuous loop as it first captures it.
        cv.imshow('frame', frame)
        if(cv.waitKey(1) == ord('q')):
          break
    cap.release()
    cv.destroyAllWindows()

def start_camera_pothole(camera_index):
    global camera_running, latest_result
    camera_running = True
    args=parse_arguments()
    cap = cv.VideoCapture(camera_index)

    #Setting the resolution of the webcam
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.webcam_resolution[0])
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.webcam_resolution[1])

    while camera_running:
        #Captures the frame
        ret, frame = cap.read()
        if not ret:
            break
        
        #Calls the prediction function
        latest_result = prediction_pothole(frame)
        frame = annotate_frame_pothole(frame, latest_result)

        pothole_detected = len(latest_result.get('predictions', [])) > 0
        socketio.emit('latest_result', {'pothole':pothole_detected})
        socketio.sleep(1)

        #Displays the frame in continuous loop as it first captures it.
        cv.imshow('frame', frame)
        if(cv.waitKey(1) == ord('q')):
          break
    cap.release()
    cv.destroyAllWindows()

def start_camera_both(camera_index):
    global camera_running, latest_result
    camera_running = True
    args=parse_arguments()
    cap = cv.VideoCapture(camera_index)

    #Setting the resolution of the webcam
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.webcam_resolution[0])
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.webcam_resolution[1])

    while camera_running:
        #Captures the frame
        ret, frame = cap.read()
        if not ret:
            break
        
        #Calls the prediction function for both traffic and pothole
        traffic_result = prediction_traffic(frame)
        pothole_result = prediction_pothole(frame)
        
        #Annotate the frame for both traffic and pothole
        frame = annotate_frame_traffic(frame, traffic_result)
        frame = annotate_frame_pothole(frame, pothole_result)

        #Check if pothole is detected
        pothole_detected = len(pothole_result.get('predictions', [])) > 0
        socketio.emit('latest_result', {'result': traffic_result, 'pothole': pothole_detected})
        socketio.sleep(1)

        #Displays the frame in continuous loop as it first captures it.
        cv.imshow('frame', frame)
        if(cv.waitKey(1) == ord('q')):
          break
    cap.release()
    cv.destroyAllWindows()

def list_available_cameras():
    index = 0
    available_cameras = []
    while True:
        cap = cv.VideoCapture(index)
        if not cap.read()[0]:
            break
        available_cameras.append(index)
        cap.release()
        index += 1
    return available_cameras

def stop_camera():
    global camera_running
    camera_running = False


