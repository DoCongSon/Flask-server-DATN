from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from pyzbar import pyzbar
import cv2
from flask_socketio import SocketIO

app = Flask('hello')
CORS(app)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
camera = None
scanning_enabled = False

def open_camera():
    global camera
    camera = cv2.VideoCapture(2, cv2.CAP_DSHOW)

def close_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None

def gen_frames():
    while True:
        if scanning_enabled and camera is not None:
            success, frame = camera.read()
            if not success:
                break
            else:
                # giảm size frame 
                frame = cv2.resize(frame, (640, 480))
                barcodes = pyzbar.decode(frame)
                if barcodes:
                    qr_data = []
                    for barcode in barcodes:
                        (x, y, w, h) = barcode.rect
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        barcodeData = barcode.data.decode("utf-8")
                        barcodeType = barcode.type
                        text = "{} ({})".format(barcodeData, barcodeType)
                        qr_data.append({"data": barcodeData, "type": barcodeType})
                        cv2.putText(frame, text, (x-10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    send_qr_data(qr_data)  # Send QR data to all connected clients
        else:
            frame = cv2.imread("./no-camera.jpg")
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index(): 
    return jsonify({ "message": "this is api qr code!" })

@app.route('/toggle_scanning', methods=['GET', 'POST'])
def toggle_scanning():
    global scanning_enabled
    if request.method == 'POST':
        scanning_enabled = not scanning_enabled
        if scanning_enabled and camera is None:
            open_camera()
        elif not scanning_enabled and camera is not None:
            close_camera()
        return ""
    return jsonify({ "camera": scanning_enabled })

def send_qr_data(qr_data):
    socketio.emit('qr_data', qr_data)  # Send QR data to all connected clients

@socketio.on('connect')
def test_connect():
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    close_camera()
