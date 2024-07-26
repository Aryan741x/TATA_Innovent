from flask import Flask
from routes import routes
from flask_cors import CORS
from app.socketio_instance import socketio

app = Flask(__name__)
CORS(app)

app.register_blueprint(routes)
socketio.init_app(app)

if __name__ == '__main__':
    socketio.run(app, debug=True)
