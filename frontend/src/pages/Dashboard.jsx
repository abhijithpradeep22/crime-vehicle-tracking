import { useState, useEffect } from "react";
import { apiRequest } from "../api/client";

export default function Dashboard() {

  const [officerName, setOfficerName] = useState("");
  const [vehicleNumber, setVehicleNumber] = useState("");
  const [caseId, setCaseId] = useState("");

  const [routeData, setRouteData] = useState(null);
  const [trackingInfo, setTrackingInfo] = useState(null);

  const [pollingId, setPollingId] = useState(null);

  // Load saved data after refresh
  useEffect(() => {

    const savedRoute = localStorage.getItem("routeData");
    const savedTracking = localStorage.getItem("trackingInfo");

    if (savedRoute) setRouteData(JSON.parse(savedRoute));
    if (savedTracking) setTrackingInfo(JSON.parse(savedTracking));

  }, []);

  const createCase = async () => {

    try {

      const res = await apiRequest("/cases/", "POST", {
        officer_id: officerName,
        target_vehicle: vehicleNumber
      });

      alert("Case created with ID: " + res.id);

      setCaseId(res.id);

    } catch (err) {

      console.error(err);
      alert("Error creating case");

    }

  };

  const startTracking = async () => {

    try {

      // Stop previous polling if exists
      if (pollingId) {
        clearInterval(pollingId);
      }

      await apiRequest("/tracking/start", "POST", {
        case_id: Number(caseId),
        target_plate: vehicleNumber
      });

      const interval = setInterval(async () => {

        try {

          const route = await apiRequest(`/tracking/route/${caseId}`);
          setRouteData(route);
          localStorage.setItem("routeData", JSON.stringify(route));

          const latest = await apiRequest(`/tracking/latest/${caseId}`);
          setTrackingInfo(latest);
          localStorage.setItem("trackingInfo", JSON.stringify(latest));

          if (latest.status === "completed") {
            clearInterval(interval);
          }

        } catch (err) {
          console.error("Polling error:", err);
        }

      }, 3000);

      setPollingId(interval);

    } catch (err) {

      console.error(err);
      alert("Tracking failed");

    }

  };

  return (

    <div>

      <h2>Dashboard</h2>

      <h3>Create Case</h3>

      <input
        placeholder="Officer Name"
        value={officerName}
        onChange={(e) => setOfficerName(e.target.value)}
      />

      <input
        placeholder="Vehicle Number"
        value={vehicleNumber}
        onChange={(e) => setVehicleNumber(e.target.value)}
      />

      <button onClick={createCase}>
        Create Case
      </button>

      <hr />

      <h3>Start Tracking</h3>

      <input
        placeholder="Case ID"
        value={caseId}
        onChange={(e) => setCaseId(e.target.value)}
      />

      <button onClick={startTracking}>
        Start Tracking
      </button>

      {trackingInfo && (

        <div>

          <h3>Tracking Status</h3>

          <p>
            Status:{" "}
            <span
              style={{
                color: trackingInfo.status === "completed" ? "green" : "red",
                fontWeight: "bold"
              }}
            >
              {trackingInfo.status === "completed" ? "COMPLETED" : "LIVE"}
            </span>
          </p>

          <p>
            Cameras Active: {trackingInfo.total_cameras || 4}
          </p>

          <p>
            Last Detection Camera: <b>{trackingInfo.latest_camera || "N/A"}</b>
          </p>

          <p>
            Location: <b>{trackingInfo.latest_location || "Unknown"}</b>
          </p>

          <p>
            Detection Time:{" "}
            <b>
              {trackingInfo.latest_event_time
                ? new Date(trackingInfo.latest_event_time).toLocaleString()
                : "N/A"}
            </b>
          </p>

          <p>
            Target Plate: {trackingInfo.target_plate || vehicleNumber}
          </p>

        </div>

      )}

      {routeData && routeData.stops && (

        <div>

          <h3>Reconstructed Route</h3>

          <pre>
            {JSON.stringify(routeData, null, 2)}
          </pre>

        </div>

      )}

    </div>

  );

}