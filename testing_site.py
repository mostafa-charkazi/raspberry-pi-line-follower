from flask import Flask, render_template, jsonify,url_for, request

app = Flask(__name__)


control_mode = "manual"

@app.route("/")
def home():
    return render_template("panel1.html")

@app.route("/joystick", methods=["POST"])
def joystick():
    try:
        f = request.form
        vx = float(f.get("vx", 0.0))   # -1.0 .. 1.0
        vy = float(f.get("vy", 0.0))   # -1.0 .. 1.0
        speed = float(f.get("speed", 0.0))  # 0.0 .. 100.0
        print(f"vx={vx}, vy={vy}, speed={speed}")
        return "OK"

    except Exception as e:
        print(f"[ERROR] Joystick: {e}")
        return f"ERROR: {e}", 500

@app.route("/ptz", methods=["POST"])
def ptz():
    direction = request.form.get("direction")
    print(f"[PTZ] {direction}")
    return f"PTZ moved {direction}"

@app.route("/mode", methods=["POST"])
def mode():
    global control_mode
    control_mode = request.form.get("mode")
    print(f"[MODE] {control_mode}")

    return control_mode

@app.route("/emergency_stop", methods=["POST"])
def emergency_stop():
    print("[EMERGENCY STOP]")
    return "STOPPED"

@app.route("/health")
def health():
    return "OK"


@app.route('/check_status')
def check_status():
    return jsonify({
        'battery': 78,
        'link': 'WiFi',
        'ir_sensors': {
            'left': 0,
            'center': 1,
            'right': 0
        }
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
    # app.run(port=5000, debug=True)
