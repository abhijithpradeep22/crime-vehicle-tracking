import { MapContainer, TileLayer, Marker, Polyline, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import iconUrl from "leaflet/dist/images/marker-icon.png";
import iconRetinaUrl from "leaflet/dist/images/marker-icon-2x.png";
import shadowUrl from "leaflet/dist/images/marker-shadow.png";

const DefaultIcon = L.icon({
  iconUrl,
  iconRetinaUrl,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

export default function RouteMap({ stops }) {

  if (!stops || stops.length === 0) {
    return <div style={{ padding: 20 }}>No route data</div>;
  }

  const positions = stops.map(s => [s.latitude, s.longitude]);
  const createNumberedIcon = (number) =>
    L.divIcon({
        html: `<div class="route-marker">${number}</div>`,
        className: "",
        iconSize: [30, 30]
    });

  return (
    <MapContainer
      center={positions[0]}
      zoom={12}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        attribution="© OpenStreetMap"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {stops.map((s, i) => (
        <Marker
            key={i}
            position={[s.latitude, s.longitude]}
            icon={createNumberedIcon(i + 1)}
        >
          <Popup>
            <b>{s.location}</b><br />
            First Seen: {new Date(s.first_seen).toLocaleString()}<br />
            Detections: {s.total_detections}
          </Popup>
        </Marker>
      ))}

      <Polyline positions={positions} />
    </MapContainer>
  );
}