import { useState, useEffect } from "react";
import { apiRequest } from "../api/client";
import { useNavigate } from "react-router-dom";
import "./Dashboard.css";

export default function Dashboard() {

  const [userId, setUserId] = useState(null);

  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);

  const [vehicleNumber, setVehicleNumber] = useState("");

  const [trackingInfo, setTrackingInfo] = useState(null);
  const [routeData, setRouteData] = useState(null);

  const [livePolling, setLivePolling] = useState(null);
  const [routePolling, setRoutePolling] = useState(null);

  const [cameraList, setCameraList] = useState([]);
  const [selectedCameras, setSelectedCameras] = useState([]);

  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);

  const [popupImage, setPopupImage] = useState(null);

  const [trackingStarted, setTrackingStarted] = useState(false);

  const navigate = useNavigate();


  /* LOAD USER */

  useEffect(() => {
    const id = localStorage.getItem("user_id");
    setUserId(id);
  }, []);


  /* LOAD CASES */

  useEffect(() => {

    if (!userId) return;

    const loadCases = async () => {
      try {
        const data = await apiRequest(`/cases/user/${userId}`);
        setCases(data);
      } catch (err) {
        console.error(err);
      }
    };

    loadCases();

  }, [userId]);


  /* LOAD CAMERAS */

  useEffect(() => {

    const loadCameras = async () => {

      try {
        const data = await apiRequest("/cameras");
        setCameraList(data);
      } catch (err) {
        console.error(err);
      }

    };

    loadCameras();

  }, []);


  /* CAMERA TOGGLE */

  const toggleCamera = (id) => {

    if (selectedCameras.includes(id)) {
      setSelectedCameras(selectedCameras.filter(c => c !== id));
    } else {
      setSelectedCameras([...selectedCameras, id]);
    }

  };


  /* LOAD REPORTS */

  const loadReports = async (caseId) => {

    try {

      const data = await apiRequest(`/reports/case/${caseId}`);
      setReports(data);

      if (data.length > 0) {
        const report = await apiRequest(`/reports/${data[0].id}`);
        setSelectedReport(report);
      }

    } catch (err) {

      console.error(err);

    }

  };


  /* OPEN CASE */

  const openCase = async (caseId) => {

    try {

      if (livePolling) clearInterval(livePolling);
      if (routePolling) clearInterval(routePolling);

      setTrackingStarted(false);
      setTrackingInfo(null);
      setRouteData(null);
      setSelectedReport(null);
      setSelectedCameras([]);

      const caseData = cases.find(c => c.id === caseId);

      setSelectedCase(caseData);
      setVehicleNumber(caseData?.target_vehicle || "");

      await loadReports(caseId);

      const latest = await apiRequest(`/tracking/latest/${caseId}`);

      if (latest && latest.status === "running") {

        setTrackingStarted(true);
        setTrackingInfo(latest);

        startPolling(caseId);

      }

    } catch (err) {

      console.error("Failed loading case", err);

    }

  };


  /* CREATE CASE */

  const createCase = async () => {

    if (!vehicleNumber || vehicleNumber.trim() === "") {

      alert("Vehicle number is required");
      return;

    }

    try {

      const res = await apiRequest("/cases/", "POST", {

        user_id: Number(userId),
        target_vehicle: vehicleNumber

      });

      setSelectedCase(res);
      setCases(prev => [res, ...prev]);

      setTrackingStarted(false);
      setTrackingInfo(null);
      setRouteData(null);
      setSelectedCameras([]);

    } catch (err) {

      console.error(err);
      alert("Case creation failed");

    }

  };


  /* START TRACKING */

  const startTracking = async () => {

    if (!selectedCase) {
      alert("Create or select a case first");
      return;
    }

    if (selectedCameras.length === 0) {
      alert("Select at least one camera");
      return;
    }

    try {

      await apiRequest("/tracking/start", "POST", {

        case_id: selectedCase.id,
        target_plate: vehicleNumber,
        camera_ids: selectedCameras

      });

      setTrackingStarted(true);

      startPolling(selectedCase.id);

    } catch (err) {

      console.error(err);

    }

  };


  /* STOP TRACKING */

  const stopTracking = async () => {

    if (!selectedCase) {
      alert("No active case");
      return;
    }

    try {

      await apiRequest(`/tracking/stop/${selectedCase.id}`, "POST");

      if (livePolling) clearInterval(livePolling);
      if (routePolling) clearInterval(routePolling);

      setTrackingStarted(false);
      setTrackingInfo(null);

      alert("Tracking stopped");

    } catch (err) {

      console.error(err);

    }

  };


  /* SAVE REPORT */

  const saveReport = async () => {

    if (!selectedCase) {

      alert("Select a case first");
      return;

    }

    if (!routeData?.stops?.length) {

      alert("No route data yet");
      return;

    }

    try {

      await apiRequest(`/reports/save/${selectedCase.id}`, "POST");

      alert("Report saved successfully");

      loadReports(selectedCase.id);

    } catch (err) {

      console.error(err);

    }

  };


  /* POLLING */

  const startPolling = (caseId) => {

    if (livePolling) clearInterval(livePolling);
    if (routePolling) clearInterval(routePolling);

    const live = setInterval(async () => {

      try {

        const latest = await apiRequest(`/tracking/latest/${caseId}`);
        setTrackingInfo(latest);

      } catch {}

    }, 3000);


    const route = setInterval(async () => {

      try {

        const data = await apiRequest(`/tracking/route/${caseId}`);
        setRouteData(data);

      } catch {}

    }, 9000);

    setLivePolling(live);
    setRoutePolling(route);

  };


  /* LOGOUT */

  const handleLogout = () => {

    if (livePolling) clearInterval(livePolling);
    if (routePolling) clearInterval(routePolling);

    localStorage.removeItem("user_id");
    localStorage.removeItem("username");

    navigate("/");

  };


  /* UI */

  return (

<div className="dashboard">


{/* HEADER */}

<div className="header">

<div className="header-left">
<span className="status-dot"/>
<span className="officer-label">
{localStorage.getItem("username")?.toUpperCase() || "OFFICER"}
</span>
</div>

<div className="header-title">
Multi-Camera Crime Vehicle Detection System
</div>

<button className="logout-btn" onClick={handleLogout}>
LOGOUT
</button>

</div>



{/* TOP PANELS */}

<div className="top-panels">


{/* CASE PANEL */}

<div className="panel">

<p className="panel-title">Register New Case</p>

<input
className="field-input"
placeholder="Target Vehicle Number"
value={vehicleNumber}
onChange={(e) => setVehicleNumber(e.target.value)}
/>

<button className="btn btn-primary" onClick={createCase}>
Create Case
</button>

{selectedCase && (

<div className="active-case">

<span className="case-label">Active Case</span>
<span className="case-id">#{selectedCase.id}</span>
<span className="case-vehicle">{selectedCase.target_vehicle}</span>

</div>

)}

<div className="divider"/>

<p className="panel-title">Tracking Control</p>

<button
className="btn btn-track"
onClick={startTracking}
disabled={trackingStarted}
>
Start Tracking
</button>

<button
className="btn btn-stop"
onClick={stopTracking}
disabled={!trackingStarted}
>
Stop Tracking
</button>

<button
className="btn btn-save"
onClick={saveReport}
disabled={!routeData?.stops?.length}
>
Save Report
</button>

</div>


{/* LIVE TRACKING */}

<div className="panel">

<p className="panel-title">Live Tracking</p>

{trackingInfo ? (

<div className="info-grid">

<div className="info-row">
<span className="info-label">Target Plate</span>
<span className="info-value plate-val">{trackingInfo.target_plate}</span>
</div>

<div className="info-row">
<span className="info-label">Latest Camera</span>
<span className="info-value">{trackingInfo.latest_camera || "—"}</span>
</div>

<div className="info-row">
<span className="info-label">Latest Location</span>
<span className="info-value">{trackingInfo.latest_location || "—"}</span>
</div>

<div className="info-row">
<span className="info-label">Last Detection</span>
<span className="info-value">
{trackingInfo.latest_event_time
? new Date(trackingInfo.latest_event_time).toLocaleString()
: "N/A"}
</span>
</div>

</div>

) : (

<p className="empty">No active tracking</p>

)}

</div>


{/* HISTORY */}

<div className="panel">

<p className="panel-title">Investigation History</p>

<div className="case-list">

{cases.map(c => (

<div
key={c.id}
className="case-item"
onClick={() => openCase(c.id)}
>

<span className="case-id">#{c.id}</span>
<span className="case-plate">{c.target_vehicle}</span>

</div>

))}

</div>

</div>

</div>


{/* CAMERA SECTION */}

<div className="camera-section">

<p className="section-title">Select Cameras</p>

<div className="camera-grid">

{cameraList.map(cam => (

<label
key={cam.camera_id}
className={`cam-chip ${
selectedCameras.includes(cam.camera_id) ? "cam-chip--on" : ""
}`}
>

<input
type="checkbox"
checked={selectedCameras.includes(cam.camera_id)}
onChange={() => toggleCamera(cam.camera_id)}
/>

{cam.camera_id} — {cam.location}

</label>

))}

</div>

</div>


{/* ROUTE */}

<div className="route-section">

<p className="section-title">Route Reconstruction</p>

{routeData?.stops?.length > 0 ? (

<div className="route-track">

{routeData.stops.map((stop, i) => (

<div key={i} className="route-stop">

<div className="stop-marker">

<span className="stop-num">{i + 1}</span>

{i < routeData.stops.length - 1 && (
<span className="stop-line"/>
)}

</div>

<div className="stop-info">

<span className="stop-cam">{stop.camera_id}</span>
<span className="stop-loc">{stop.location}</span>

<span className="stop-time">
{new Date(stop.first_seen).toLocaleString()}
</span>

<span
className="stop-sighting"
onClick={() => setPopupImage(stop.representative_vehicle_image)}
>
View Sighting
</span>

</div>

</div>

))}

</div>

) : (

<p className="empty">No route data yet</p>

)}

</div>

{/* INVESTIGATION REPORT */}

{selectedReport && (

<div className="report-view">

<h2>Investigation Report</h2>

<p><strong>Case ID:</strong> {selectedReport.case_id}</p>

{selectedReport.stops.map((stop, i) => (

<div key={i} className="report-stop">

<h4>{i + 1}. {stop.camera_id} — {stop.location}</h4>

<p>First Seen: {new Date(stop.first_seen).toLocaleString()}</p>

<p>Detections: {stop.total_detections}</p>

{stop.travel_minutes_from_previous && (

<p className="travel-time">
↓ Travel Time: {stop.travel_minutes_from_previous} minutes
</p>

)}

<div className="report-images">

<img
src={`http://127.0.0.1:8000${stop.representative_vehicle_image}`}
alt="vehicle"
/>

<img
src={`http://127.0.0.1:8000${stop.representative_plate_image}`}
alt="plate"
/>

</div>

</div>

))}

</div>

)}

{/* IMAGE POPUP */}

{popupImage && (

<div className="image-popup">

<div className="image-popup-content">

<button
className="close-btn"
onClick={() => setPopupImage(null)}
>
✕
</button>

<img
src={`http://127.0.0.1:8000${popupImage}`}
alt="Vehicle"
/>

</div>

</div>

)}

</div>

  );

}