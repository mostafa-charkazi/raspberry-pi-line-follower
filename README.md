# Raspberry Pi--Based Autonomous Vehicle

Embedded Systems \| Computer Vision \| Web Interface

## 📌 Project Overview

This repository contains the implementation of a course project
developed in the Department of Electrical Engineering at Shahid Beheshti
University.

The project presents the design and implementation of a small-scale
autonomous vehicle built on the Raspberry Pi platform. The system
integrates real-time image processing, IR-based line following, embedded
motor control, and a web-based monitoring and control interface.

The vehicle supports multiple operating modes:

-   Manual (Joystick-based control via browser)
-   IR Sensor Mode (Line follower)
-   Image Processing Mode (Camera-based navigation)
-   Sensor + Camera Fusion Mode

------------------------------------------------------------------------

## 🏗 System Architecture

The system consists of four tightly integrated subsystems:

1.  Perception -- Camera module and IR sensors
2.  Control -- Embedded Python control logic
3.  Actuation -- DC motors driven via PWM (GPIO)
4.  User Interface -- Flask-based web Human--Machine Interface

The Raspberry Pi acts as the central processing and control unit.

------------------------------------------------------------------------

## 🧠 Image Processing & Control

The visual processing pipeline includes:

-   Frame acquisition via Picamera2
-   Frame resizing and grayscale preprocessing
-   Gaussian filtering
-   Binary thresholding
-   Contour detection
-   Error calculation relative to frame center
-   Motion command generation (vx, vy, speed)

The system implements a closed-loop perception--control structure
enabling adaptive navigation.

A sensor--camera fusion strategy is also implemented to improve
robustness and reliability in line tracking scenarios.

------------------------------------------------------------------------

## 🌐 Web-Based Interface

A responsive browser-based interface was developed using Flask, HTML,
CSS, and JavaScript.

Features:

-   Real-time manual control
-   Mode switching (Manual / Sensor / Camera / Fusion)
-   Emergency stop function
-   System status monitoring
-   UX-focused layout for safe and intuitive operation

------------------------------------------------------------------------

## 📄 Project Report
Available at:

docs/paper.pdf

The document summarizes system design, hardware architecture, software
implementation, and experimental evaluation.

------------------------------------------------------------------------

## 🎥 Demonstration

LinkedIn Post:
https://www.linkedin.com/feed/update/urn:li:activity:7428501203162013696/

Project Video:
https://www.linkedin.com/feed/update/urn:li:activity:7428504409505943552/

------------------------------------------------------------------------

## 🛠 Technologies Used

-   Raspberry Pi
-   Python
-   Flask
-   OpenCV
-   Picamera2
-   RPi.GPIO
-   NumPy

------------------------------------------------------------------------

## 🚀 Installation

Install required dependencies:

pip install -r requirements.txt

------------------------------------------------------------------------

## ▶ Running the Application

python3 app.py

Server runs on:

http://`<raspberry-pi-ip>`{=html}:4580

------------------------------------------------------------------------

## 📂 Project Structure

    raspberry-pi-line-follower/
    │
    ├── main.py
    ├── testing_site.py
    ├── requirements.txt
    ├── README.md
    │
    ├── templates/
    │   └── panel1.html
    │
    ├── static/
    │   ├── styles.css
    │   └── script.js
    │   └── status-updater.js
    │
    ├── docs/
    │   └── paper.pdf


------------------------------------------------------------------------

## 📜 License

This project was developed for academic and educational purposes.
