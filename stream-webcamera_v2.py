from flask import Flask, render_template, Response, jsonify
from flask_cors import CORS, cross_origin
from pyzbar import pyzbar
import cv2

app = Flask('hello')
CORS(app, support_credentials=True)
camera = cv2.VideoCapture(2, cv2.CAP_DSHOW)
scanning_enabled = True

def open_camera():
    global camera
    camera = cv2.VideoCapture(2, cv2.CAP_DSHOW)

def close_camera():
    global camera
    if camera is not None:
        camera.release()
        camera = None
# ... (previous code)

def gen_frames():  
    while True:
        if scanning_enabled and camera is not None:
            success, frame = camera.read()
            if not success:
                break
            else:
                barcodes = pyzbar.decode(frame)
                if barcodes:
                    qr_data = []
                    for barcode in barcodes:
                        barcodeData = barcode.data.decode("utf-8")
                        barcodeType = barcode.type
                        qr_data.append({"data": barcodeData, "type": barcodeType})
                        (x, y, w, h) = barcode.rect
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                        cv2.putText(frame, "{} ({})".format(barcodeData, barcodeType), (x-10, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                else:
                    qr_data = None
        else:
            frame = cv2.imread("./error.jpg")
            qr_data = None

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return """
<body>
<div class="container">
    <div class="row">
        <div class="col-lg-8  offset-lg-2">
            <h3 class="mt-5">Live Streaming</h3>
            <img src="/video_feed" width="100%">
            <form action="/toggle_scanning" method="post">
                <button type="submit" class="btn btn-primary mt-3">{}</button>
            </form>
        </div>
    </div>
</div>
</body>
""".format("Stop Scanning" if scanning_enabled else "Start Scanning")

@app.route('/toggle_scanning', methods=['POST'])
def toggle_scanning():
    global scanning_enabled
    scanning_enabled = not scanning_enabled
    if scanning_enabled and camera is None:
        open_camera()
    elif not scanning_enabled and camera is not None:
        close_camera()
    return ""

@app.route('/qr_data')
def json_data():
    if scanning_enabled and camera is not None:
        success, frame = camera.read()
        if success:
            barcodes = pyzbar.decode(frame)
            if barcodes:
                qr_data = []
                for barcode in barcodes:
                    barcodeData = barcode.data.decode("utf-8")
                    barcodeType = barcode.type
                    qr_data.append({"data": barcodeData, "type": barcodeType})
                return jsonify(qr_data)
    return jsonify([{ "data": None, "type": None }])

@app.route('/incomes')
def get_incomes():
    incomes = [
        { 'description': 'salary', 'amount': 5000 }
    ]
    return jsonify(incomes)

if __name__ == '__main__':
    app.run()
    close_camera()
