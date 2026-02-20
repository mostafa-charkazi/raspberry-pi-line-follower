#Abbaspour | Embedded | Email Title 
#rpicam-hello -t 0 --width 640 --height 480 --framerate 40
#.venv/bin/python app.py
#!/usr/bin/env python3
#!/usr/bin/env python3
import time
import flask
import RPi.GPIO as GPIO
import atexit
import signal
import threading
import picamera2 
import cv2
import numpy as np
from libcamera import Transform


app = flask.Flask(__name__)
camera = picamera2.Picamera2()

config = camera.create_video_configuration(
    main={"size": (320, 240), "format": "RGB888"},
    transform=Transform(vflip=True, hflip=True)
)

camera.configure(config)



# ---------- GPIO SETUP ----------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

RIGHT_DIR = 2

LEFT_DIR  = 3
RIGHT_PWM = 12   # Pin 32 (PWM0)
LEFT_PWM  = 18   # Pin 12 (PWM0)

IR_RIGHT = 22
IR_LEFT = 27
IR_CENTER = 17

FREQ = 10000

# Setup pins
GPIO.setup(IR_RIGHT, GPIO.IN)
GPIO.setup(IR_LEFT, GPIO.IN)
GPIO.setup(IR_CENTER, GPIO.IN)

GPIO.setup(RIGHT_DIR, GPIO.OUT)
GPIO.setup(LEFT_DIR, GPIO.OUT)
GPIO.setup(RIGHT_PWM, GPIO.OUT)
GPIO.setup(LEFT_PWM, GPIO.OUT)

# Initial direction
GPIO.output(RIGHT_DIR, GPIO.HIGH)  # Forward
GPIO.output(LEFT_DIR, GPIO.LOW)    # Forward

# PWM setup
pwm_r = GPIO.PWM(RIGHT_PWM, FREQ)
pwm_l = GPIO.PWM(LEFT_PWM, FREQ)

pwm_r.start(0)
pwm_l.start(0)

# Global variables for speed smoothing
current_speed = 0.0
speed_lock = threading.Lock()

# Global variables for control_mode
control_mode = "manual"

last_error = 0
def line_detection(frame , THRESHOLD_VALUE=55, HEIGHT=120, CENTER=150, MIN_CONTOUR_AREA=500):

  
    frame = cv2.resize(frame, (320, 240))
    height, width, _ = frame.shape

   
    gray = frame[HEIGHT:height, :, 0]
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blur, THRESHOLD_VALUE, 255, cv2.THRESH_BINARY_INV)

   
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cx = 0
    error = 400
    frame_center = CENTER

    if contours:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) > MIN_CONTOUR_AREA:
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                error = cx - frame_center


    print(f"Center X: {cx}")
    print(f"Error: {error}")


    return error 


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))

def stop_all():
    global current_speed
    with speed_lock:
        current_speed = 0.0
    pwm_r.ChangeDutyCycle(0)
    pwm_l.ChangeDutyCycle(0)
    print("[STOP] All motors stopped")

def cleanup():
    print("[CLEANUP] Cleaning up GPIO...")
    stop_all()
    pwm_r.stop()
    pwm_l.stop()
    GPIO.cleanup()

def read_ir():
    print(":hjkdsvhjkdshvjdshvsdhv")
    L = GPIO.input(IR_LEFT)
    C = GPIO.input(IR_CENTER)
    R = GPIO.input(IR_RIGHT)
    return {"R":R, "C":C, "L":L}

def set_pwm(vx, vy, speed):
    try:     
	# Smooth speed update: speed_new = 0.55*speed + 0.45*current_speed
        with speed_lock:
            # If speed is received as 0-100, convert to 0-1 range
            speed_normalized = speed/100
            # speed_normalized = clamp(speed_normalized, 0.0, 1.0)
            current_speed = abs((0.55 * speed_normalized + 0.45))
            current_speed=current_speed*.9
        # Deadzone for joystick
        DEAD = 0.05
        if abs(vx) < DEAD: vx = 0.0
        if abs(vy) < DEAD: vy = 0.0
        
        # Set direction based on Vy
        if vy > 0:
            # Forward mode
            GPIO.output(RIGHT_DIR, GPIO.HIGH)
            GPIO.output(LEFT_DIR, GPIO.LOW)
        elif vy < 0:
            # Reverse mode
            GPIO.output(RIGHT_DIR, GPIO.LOW)
            GPIO.output(LEFT_DIR, GPIO.HIGH)
        
        # If both vx and vy are 0, stop
        if vx == 0 and vy == 0:
            pwm_r.ChangeDutyCycle(0)
            pwm_l.ChangeDutyCycle(0)
            print(f"[JOY] Stopped | Speed={current_speed:.2f}")
            return "OK"
        
        # Calculate PWM values based on Vx
        if vx > .1:
            # Turning right
            pwm_left_val = ((-100 * vx + 100) * current_speed )*.1
            pwm_right_val = ((-40 * vx + 100) * current_speed)+20 #-50 was ok
        elif vx < -.1:
            # Turning left
            pwm_left_val = ((35 * vx + 100) * current_speed  ) +25# 50 before
            pwm_right_val = ((100 * vx + 100) * current_speed )*.1 
        else:
            # Straight movement (vx = 0)
            pwm_left_val = 100 * current_speed *.5
            pwm_right_val = 100 * current_speed *.5

        # Clamp PWM values to 0-100
        pwm_left_val = clamp(pwm_left_val, 0, 100)
        pwm_right_val = clamp(pwm_right_val, 0, 100)
        
        # Apply PWM
        pwm_r.ChangeDutyCycle(pwm_right_val)
        pwm_l.ChangeDutyCycle(pwm_left_val)
        
        print(f"[JOY] vx={vx:.2f} vy={vy:.2f} speed={current_speed:.2f} -> L={pwm_left_val:.1f}% R={pwm_right_val:.1f}%")
        return "OK"
    except:
        return "Error assigning pwm"

# # Register cleanup for exit
# atexit.register(cleanup)
# signal.signal(signal.SIGTERM, lambda s, f: cleanup())
# signal.signal(signal.SIGINT, lambda s, f: cleanup())

# ---------- ROUTES ----------
@app.route("/")
def homepage():
    return flask.render_template("panel1.html")

@app.route("/joystick", methods=["POST"])
def joystick():
    try:
        global control_mode
        if control_mode == "manual":
            global current_speed

            f = flask.request.form
            vx = float(f.get("vx", 0.0))   # -1.0 .. 1.0
            vy = float(f.get("vy", 0.0))   # -1.0 .. 1.0
            speed = float(f.get("speed", 0.0))  # 0.0 .. 100.0
            speed=speed*.8
            set_pwm(vx, vy, speed)

        return "OK"

    except Exception as e:
        print(f"[ERROR] Joystick: {e}")
        return f"ERROR: {e}", 500

@app.route("/ptz", methods=["POST"])
def ptz():
    direction = flask.request.form.get("direction")
    print(f"[PTZ] {direction}")
    return f"PTZ moved {direction}"

@app.route("/mode", methods=["POST"])
def mode():
    global control_mode
    control_mode = flask.request.form.get("mode")
    print(f"[MODE] {control_mode}")

    if control_mode == 'manual':
        # stop_all() # we should not stop motors here
        pass
    elif control_mode == 'sensor':
        last_vx=0
        while True:
            if control_mode != "sensor":
                stop_all()
                break
            else:


                IR = read_ir()
                vy = -1

                # Ø³Ø±Ø¹Øªâ€ŒÙ‡Ø§ (Ø§Ù„Ú¯ÙˆÛŒ Ø±Ø§ÛŒØ¬)
                STRAIGHT = 100 #35
                TURN_FAST = 100 #95

                TURN_SUPERFAST= 25 #70

                L = IR["L"]
                C = IR["C"]
                R = IR["R"]

                # Ù¾ÛŒØ´â€ŒÙØ±Ø¶
                vx = 0
                speed = STRAIGHT

                # -------- Line Follower Logic --------

                if L == 0 and C == 1 and R == 0:
                    # Ø®Ø· Ø¯Ù‚ÛŒÙ‚Ø§Ù‹ ÙˆØ³Ø·
                    vx = 0
                    speed = STRAIGHT
                    print("010")
                elif L == 0 and C == 0 and R == 1:
                    # Ù¾ÛŒÚ† ØªÙ†Ø¯ Ø±Ø§Ø³Øª
                    vx = 1
                    speed = TURN_FAST
                    last_vx = 1
                    print("001")
                elif L == 0 and C == 1 and R == 1:
                    # Ù¾ÛŒÚ† Ù†Ø±Ù… Ø±Ø§Ø³Øª (Ø®ÛŒÙ„ÛŒ Ù…Ù‡Ù…)
                    vx = 1   #.5
                    speed = TURN_SUPERFAST #SOFT
                    last_vx = 1
                    print("011")

                elif L == 1 and C == 0 and R == 0:
                    # Ù¾ÛŒÚ† ØªÙ†Ø¯ Ú†Ù¾
                    vx = -1
                    speed = TURN_FAST
                    last_vx = -1
                    print("100")


                elif L == 1 and C == 1 and R == 0:
                    # Ù¾ÛŒÚ† Ù†Ø±Ù… Ú†Ù¾
                    vx = -1 #-.5
                    speed = TURN_SUPERFAST #SOFT
                    last_vx = -1
                    print("110")

                elif L == 1 and C == 0 and R == 1:
                    # Ø®Ø· Ù¾Ù‡Ù† / ØªÙ‚Ø§Ø·Ø¹
                    vx = 0
                    speed = STRAIGHT
                    last_vx =0    #for test
                    print("101")

                elif L == 0 and C == 0 and R == 0:
                    # Ú¯Ù… Ø´Ø¯Ù† Ø®Ø· â†’ Ø§Ø¯Ø§Ù…Ù‡ Ø¢Ø®Ø±ÛŒÙ† Ø¬Ù‡Øª (Ø§Ù„Ú¯ÙˆÛŒ Ø¨Ø³ÛŒØ§Ø± Ø±Ø§ÛŒØ¬)
                    vx = last_vx
                    speed = TURN_FAST
                    print("000")
                    

                set_pwm(vx, vy, speed)





    elif control_mode == "image":
        camera.start()
        last_vx=0
        speed=30 

        while True:
             if control_mode != "image":
                 camera.stop()
                 stop_all()
                 break
             STRAIGHT = 50
             TURN_FAST = 45
             TURN_SUPERFAST= 80
          #region: Saniar
             #time.sleep(0.02)
             frame = camera.capture_array()
             err = line_detection(frame)

             print("PICTURE CAPTURED")
             #endregion
            
             print(err)
             #it has to go right
             vy=-1
             
             if err>10 and err< 400:
                 vx=1
                 speed=TURN_SUPERFAST
                 last_vx=vx
            #it has to go left    
             elif err<-45:
                 vx=-1
                 speed=TURN_SUPERFAST
                 last_vx=vx
             elif((err<=10) and (err>=-45)) :
                 vx=0
                 speed=STRAIGHT
                 print("vnvkdjvkdfjvkfdjvklfdjvkl")
                 last_vx=vx
             #elif err>-12 and err<12:
                     

             else:
                 vx=last_vx 
                 speed= STRAIGHT
                 last_vx=vx
             set_pwm(vx, vy, speed)
                      

    elif control_mode == 'sensor-camera':
        camera.start()
        last_vx = 0
        vy = -1

        # thresholds for camera error (tune)
        CAM_RIGHT_TH = 45
        CAM_LEFT_TH  = -45
        CAM_STRAIGHT_BAND = 80 # smaller = more sensitive

        # speeds
        STRAIGHT = 35
        TURN_FAST = 90
        TURN_SUPERFAST = 95
        INTERSECTION_SPEED = 30

        while True:
            if control_mode != "sensor-camera":
                camera.stop()
                stop_all()
                break

            # ---- read sensors & camera
            IR = read_ir()
            L, C, R = IR["L"], IR["C"], IR["R"]

            frame = camera.capture_array()
            err = line_detection(frame)  # might be 400 if no contour

            # ---- 1) camera-based decision (base command)
            vx_cam = 0
            speed_cam = STRAIGHT

            if err == 400:
                # camera lost line
                vx_cam = last_vx
                speed_cam = TURN_FAST
            else:
                if err > CAM_RIGHT_TH:
                    vx_cam = 1
                    speed_cam = TURN_FAST
                elif err < CAM_LEFT_TH:
                    vx_cam = -1
                    speed_cam = TURN_FAST
                elif abs(err) <= CAM_STRAIGHT_BAND:
                    vx_cam = 0
                    speed_cam = STRAIGHT
                else:
                    # medium error -> softer turn
                    vx_cam = 0.6 if err > 0 else -0.6
                    speed_cam = STRAIGHT

            # ---- 2) IR-based decision (high confidence close-to-ground truth)
            # Interpret typical 3-sensor line follower:
            # 010 -> centered
            # 001/011 -> line on right -> turn right
            # 100/110 -> line on left  -> turn left
            # 101 -> intersection / cross
            # 000 -> lost line
            vx_ir = None
            speed_ir = None
            ir_conf = 0  # 0=low, 1=medium, 2=high

            if (L, C, R) == (0, 1, 0):
                vx_ir = 0
                speed_ir = STRAIGHT
                ir_conf = 2
            elif (L, C, R) in [(0, 0, 1), (0, 1, 1)]:
                vx_ir = 1
                speed_ir = TURN_SUPERFAST
                ir_conf = 2
            elif (L, C, R) in [(1, 0, 0), (1, 1, 0)]:
                vx_ir = -1
                speed_ir = TURN_SUPERFAST
                ir_conf = 2
            elif (L, C, R) == (1, 0, 1):
                # intersection: go straight but slower, keep last_vx neutral
                vx_ir = 0
                speed_ir = INTERSECTION_SPEED
                ir_conf = 1
            elif (L, C, R) == (0, 0, 0):
                vx_ir = last_vx
                speed_ir = TURN_FAST
                ir_conf = 2

            # ---- 3) Fusion policy
            # If IR is confident -> override camera.
            # Else -> rely on camera.
            if ir_conf >= 2 and vx_ir is not None:
                vx = vx_ir
                speed = speed_ir
            elif ir_conf == 1 and vx_ir is not None:
                # intersection case: keep it simple
                vx = vx_ir
                speed = speed_ir
            else:
                vx = vx_cam
                speed = speed_cam

            # Update last_vx only when we actually turn
            if vx != 0:
                last_vx = 1 if vx > 0 else -1

            set_pwm(vx, vy, speed)


    else:
        raise "Not Allowed"
    return control_mode

@app.route("/emergency_stop", methods=["POST"])
def emergency_stop():
    stop_all()
    print("[EMERGENCY STOP]")
    return "STOPPED"

@app.route("/health")
def health():
    return "OK"


@app.route('/check_status')
def check_status():
    #IR = read_ir()
    return flask.jsonify({
        'battery': 78,
        'link': 'WiFi',
        #'ir_sensors': {
           # 'left': IR['L'],
           # 'center': IR['C'],
           # 'right': IR['R']
       # }
    })


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=4580, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        cleanup()
        print("Exiting")
    except Exception as e:
        print(f"Fatal error: {e}")
        cleanup()



