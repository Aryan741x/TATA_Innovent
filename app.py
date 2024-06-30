from flask import Flask, jsonify
from inference_sdk import InferenceHTTPClient

CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="PTWpY7UC6PzM2wjogVPf"
)

app = Flask(__name__)

@app.route('/try', methods=['GET'])
def trying():
    result = CLIENT.infer("trying.jpg", model_id="indian-traffic-signboards-a0gtk/1")
    print(result)
    return jsonify({'message': 'try successful'}), 201



if __name__ == '__main__':
    app.run(debug=True)