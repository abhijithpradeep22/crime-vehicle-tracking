# Multi-Camera Crime Vehicle Detection and Tracking System

## Overview

This project is a **Multi-Camera Crime Vehicle Detection and Tracking System** designed to assist law enforcement agencies in identifying and tracking vehicles across multiple surveillance cameras.

Traditional ANPR systems operate independently and cannot correlate vehicle movements across locations. This system addresses that limitation by integrating **vehicle detection, license plate recognition, and spatio-temporal analysis** to reconstruct the movement path of a vehicle without relying on GPS.

---

## Objectives

* Automate vehicle detection and license plate recognition from surveillance videos
* Associate vehicle detections across multiple cameras
* Reconstruct vehicle movement paths using timestamps and location data
* Reduce manual effort in crime investigation
* Provide a web-based interface for tracking and visualization

---

## Tech Stack

### Backend

* FastAPI (API framework)
* SQLAlchemy (ORM)
* OpenCV (video processing)
* YOLOv8 (vehicle and plate detection)
* PaddleOCR (text recognition)

### Frontend

* React (Vite)
* React Router
* React Leaflet (map visualization)

### Database

* SQLite (development)

---

## System Architecture

The system follows a **three-tier architecture**:

1. **Processing Layer**

   * Frame extraction using OpenCV
   * Vehicle detection using YOLOv8
   * License plate detection using a YOLO model
   * OCR using PaddleOCR
   * Validation and filtering

2. **Application Layer**

   * FastAPI backend
   * Spatio-temporal analysis
   * Route reconstruction

3. **Presentation Layer**

   * React frontend
   * Case management
   * Map-based visualization

---

## System Workflow

1. Video streams are processed frame-by-frame using OpenCV
2. YOLOv8 detects vehicles (car, bike, bus, truck)
3. A second YOLO model detects license plates within vehicles
4. Plate regions are cropped and passed to OCR
5. PaddleOCR extracts text from license plates
6. Extracted text is validated using format rules and confidence thresholds
7. Valid detections are stored in the database with:

   * timestamp
   * camera ID
   * location
   * evidence images
8. The tracking module associates detections across cameras
9. Vehicle routes are reconstructed using chronological data
10. Results are displayed on a map interface

---

## Key Features

* Multi-class vehicle detection using YOLOv8
* License plate detection and OCR
* Multi-camera vehicle tracking
* Route reconstruction without GPS
* Travel time estimation between cameras
* Tracking session management (first and latest detection)
* Evidence image storage
* Automatic camera selection based on location
* Map-based visualization of vehicle movement

---

## Database Design

The system uses a relational database with key tables:

* **Cameras** → camera details and location coordinates
* **Cases** → investigation case records
* **Vehicle Sightings** → detection records
* **Tracking Sessions** → active tracking state
* **Reports** → reconstructed route data

Each detection includes:

* plate number
* confidence
* timestamp
* camera ID
* image paths

This structure enables efficient **spatio-temporal analysis and tracking**.

---

## Core Concepts

### Two-Stage Detection

* Stage 1: Vehicle detection
* Stage 2: License plate detection within the vehicle

This approach improves OCR accuracy by reducing background noise.

---

### Spatio-Temporal Tracking

* Uses **time and camera location**
* Links detections across cameras
* Builds a movement sequence

---

### Tracking Session Model

* Stores:

  * first detection
  * latest detection
* Enables real-time monitoring

---

### Route Reconstruction

* Uses stored sightings
* Orders detections chronologically
* Groups them into meaningful stops

---

## Results

* Accurate vehicle detection using YOLOv8
* Reliable license plate recognition under normal conditions
* Successful cross-camera tracking
* Effective route reconstruction using timestamps

System testing confirms:

* Proper validation handling
* Correct tracking behavior
* Robust handling of edge cases

---

## Limitations

* Performance depends on video quality (lighting and resolution)
* OCR accuracy is affected by blur or occlusion
* SQLite is not suitable for large-scale deployments

---

## How to Run

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Author

**Abhijith P**

---

## Note

This project uses pre-trained YOLOv8 models and OCR libraries.  
The primary contribution lies in system design, multi-camera tracking logic, data integration, and spatio-temporal analysis.
