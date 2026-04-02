import { useState, useEffect } from "react";
import { apiRequest } from "../api/client";
import { useNavigate } from "react-router-dom";
import RouteMap from "../components/RouteMap";
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

  const [caseSearch, setCaseSearch] = useState("");

  const [reports, setReports] = useState([]);
  const [selectedReport, setSelectedReport] = useState(null);

  const [popupImage, setPopupImage] = useState(null);

  const [trackingStarted, setTrackingStarted] = useState(false);

  const [noMatchShown, setNoMatchShown] = useState(false);
  const [showNoMatchModal, setShowNoMatchModal] = useState(false);

  const [historyMode, setHistoryMode] = useState(false);

  const [autoLoading, setAutoLoading] = useState(false);

  const [autoMode, setAutoMode] = useState(false);
  const [locationInput, setLocationInput] = useState("");

  const [cameraSearch, setCameraSearch] = useState("");

  const [autoSelected, setAutoSelected] = useState([]);

  

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

  /* CAMERA FILTER */

  const filteredCameras = cameraList.filter(cam =>
  cam.camera_id.toLowerCase().includes(cameraSearch.toLowerCase()) ||
  cam.location.toLowerCase().includes(cameraSearch.toLowerCase())
);


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
      setAutoSelected([]);

      const caseData = cases.find(c => c.id === caseId);

      setSelectedCase(caseData);
      setHistoryMode(true);

      await loadReports(caseId);

      const route = await apiRequest(`/tracking/route/${caseId}`);

      if (route?.stops) {
        setRouteData({
          ...route,
          stops: [...route.stops]
        });
      }

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

  const trimmed = vehicleNumber.trim();

  // length validation
  if (trimmed.length <= 4 || trimmed.length >= 11) {
    alert("Vehicle number must be between 5 and 10 characters");
    return;
  }

  try {

    const res = await apiRequest("/cases/", "POST", {
      user_id: Number(userId),
      target_vehicle: trimmed,
      incident_location: null
    });

    setSelectedCase(res);
    setCases(prev => [res, ...prev]);
    setHistoryMode(false);

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

  
  if (selectedCameras.length === 0 && autoSelected.length === 0) {
    alert("No cameras selected. Please select cameras or use auto selection.");
    return;
  }

  try {

    const res = await apiRequest("/tracking/start", "POST", {
      case_id: selectedCase.id,
      target_plate: selectedCase.target_vehicle,
      camera_ids: selectedCameras.length > 0 ? selectedCameras : null
    });

    if (selectedCameras.length === 0 && res.selected_cameras) {
      setAutoSelected(res.selected_cameras);
      setSelectedCameras(res.selected_cameras);
    }

    setTrackingStarted(true);
    setNoMatchShown(false);

    startPolling(selectedCase.id);

  } catch (err) {

    console.error(err);

    if (err.response?.data?.detail) {
      alert(err.response.data.detail);
    } else {
      alert("Failed to start tracking");
    }

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
      setAutoSelected([]);
      setSelectedCameras([]);

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

      if (latest.status === "completed") {

        clearInterval(live);
        clearInterval(route);

        if (!latest.match_found) {
          setShowNoMatchModal(true);
        }

      }

    } catch (err) {
      console.error(err);
    }

  }, 4000);


  const route = setInterval(async () => {

    try {

      const latest = await apiRequest(`/tracking/latest/${caseId}`);

      // STOP ROUTE POLLING WHEN TRACKING FINISHES
      if (latest.status === "completed") {
        clearInterval(route);
        return;
      }

      const data = await apiRequest(`/tracking/route/${caseId}`);

      if (data?.stops) {
        setRouteData({
          ...data,
          stops: [...data.stops]
        });
      }

    } catch (err) {
      console.error("Route polling error:", err);
    }

  }, 6000);

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

  const filteredCases = cases.filter(c =>
    c.target_vehicle.toLowerCase().includes(caseSearch.toLowerCase())
  );



  const handleAutoSelect = async () => {

  if (!locationInput) {
    alert("Enter a location");
    return;
  }

  setAutoLoading(true);

  try {

    // Save location
    await apiRequest(`/cases/${selectedCase.id}/location`, "POST", {
      incident_location: locationInput
    });

    const res = await apiRequest(`/tracking/auto-select/${selectedCase.id}`);

  if (!res.selected_cameras || res.selected_cameras.length === 0) {
    alert("No nearby cameras found for this location");
    setAutoSelected([]);
    setSelectedCameras([]);
    return;
  }

  setAutoSelected(res.selected_cameras);
  setSelectedCameras(res.selected_cameras);

  } catch (err) {
    console.error(err);
    alert("Failed to auto select cameras");
  } finally {
    setAutoLoading(false);
  }
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
onChange={(e) => {
  let value = e.target.value.toUpperCase();

  // allow only letters and numbers
  value = value.replace(/[^A-Z0-9]/g, "");

  if (value.length > 10) {
    value = value.slice(0, 10);
  }

  setVehicleNumber(value);
}}
/>

<button className="btn btn-primary" onClick={createCase}>
Create Case
</button>
{selectedCase && (

<div className="tracking-status">

Tracking Case #{selectedCase.id} — {selectedCase.target_vehicle}

</div>

)}

<div className="divider"/>

<p className="panel-title">Tracking Control</p>

<button
className="btn btn-track"
onClick={startTracking}
disabled={trackingStarted || historyMode}
>
Start Tracking
</button>

<button
className="btn btn-stop"
onClick={stopTracking}
disabled={!trackingStarted || historyMode}
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

<input
  className="field-input"
  placeholder="Search vehicle number..."
  value={caseSearch}
  onChange={(e) => setCaseSearch(e.target.value)}
/>

<div className="case-list">

{filteredCases.map(c => (

<div
key={c.id}
className={`case-item ${selectedCase?.id === c.id ? "active" : ""}`}
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

<p className="section-title">Select Cameras</p>
 {!selectedCase && (
  <p style={{ color: "#c41230", margin: "10px 14px" }}>
    Please register a case to enable camera selection
  </p>
)}

<div className="auto-selection-panel">

  <button
    className={`btn btn-primary ${autoMode ? "btn-active" : ""}`}
    disabled={!selectedCase}
    onClick={() => {
      if (!selectedCase) return;

      setAutoMode(true);
      setSelectedCameras([]);
      setAutoSelected([]);
      setLocationInput("");
    }}
  >
    Automatic Camera Selection
  </button>

  <button
    className={`btn btn-secondary ${!autoMode ? "btn-active" : ""}`}
    disabled={!selectedCase}
    onClick={() => {
      if (!selectedCase) return;

        setAutoMode(false);
        setAutoSelected([]);

        setLocationInput("");
    }}
  >
    Manual Camera Selection
  </button>

</div>

{autoMode && selectedCase &&  (
  <div className="location-input-box">

    <input
      className="field-input location-input"
      placeholder="Enter incident location"
      value={locationInput}
      onChange={(e) => setLocationInput(e.target.value)}
    />

    <button
  className="btn btn-track"
  onClick={handleAutoSelect}
  disabled={autoLoading}
>
  {autoLoading ? "Saving..." : "Set Location"}
</button>

{selectedCase?.incident_location && (
  <p style={{ color: "green", marginTop: "5px" }}>
    Location set: {selectedCase.incident_location}
  </p>
)}

  </div>
)}





<div className={`camera-section ${!selectedCase ? "disabled-section" : ""}`}>

 



<input
  className="field-input"
  placeholder="Search cameras (ID or location)"
  value={cameraSearch}
  onChange={(e) => setCameraSearch(e.target.value)}
/>

<div className="camera-grid">

{filteredCameras.map(cam => (

<label
key={cam.camera_id}
className={`cam-chip 
  ${selectedCameras.includes(cam.camera_id) ? "cam-chip--on" : ""}
  ${autoMode && autoSelected.includes(cam.camera_id) ? "auto-highlight" : ""}
`}
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

<div className="map-panel">
  {routeData?.stops?.length > 0 && (
    <RouteMap stops={routeData.stops} />
  )}
</div>

{/* INVESTIGATION REPORT */}

{historyMode && selectedReport &&  (

<div className="report-view">

<h2>Investigation Report</h2>

<p><strong>Case ID:</strong> {selectedReport.case_id}</p>

{selectedReport.stops.map((stop, i) => (

<div key={i} className="report-stop">

<h4>{i + 1}. {stop.camera_id} — {stop.location}</h4>

<p>First Detection: {new Date(stop.first_seen).toLocaleString()}</p>

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

{/* NO VEHICLE DETECTED MODAL */}
{showNoMatchModal && (

  <div className="custom-modal-overlay">

    <div className="custom-modal">

      <h3>No Vehicle Detected</h3>

      <p>
        No vehicle with the corresponding register number was detected in the
        selected camera feeds.
      </p>

      <button
        className="btn btn-primary"
        onClick={() => setShowNoMatchModal(false)}
      >
        Close
      </button>

    </div>

  </div>

)}

</div>

  );

}