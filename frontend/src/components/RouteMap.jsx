import { motion } from "framer-motion"
import L from "leaflet"
import { MapContainer, TileLayer, Polyline, useMap, Marker, Popup } from "react-leaflet"

function FitBounds({ coordinates }) {
  const map = useMap()
  map.flyToBounds(coordinates, { padding: [80, 80], duration: 2 })
  return null
}

const redNeonIcon = new L.DivIcon({
  className: "",
  html: `<div style="width:18px;height:18px;background:#ff0033;border-radius:999px;box-shadow:0 0 20px #ff0033;border:2px solid white;"></div>`,
  iconSize: [18, 18],
})

export default function RouteMap({ routeCoordinates }) {
  if (!routeCoordinates || routeCoordinates.length === 0) return null
  return (
    <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} className="rounded-3xl overflow-hidden border border-white/10">
      <MapContainer center={routeCoordinates[0]} zoom={13} scrollWheelZoom={false} className="h-[500px] w-full">
        <FitBounds coordinates={routeCoordinates} />
        <TileLayer attribution='&copy; OpenStreetMap & CartoDB' url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
        <Marker position={routeCoordinates[0]} icon={redNeonIcon}><Popup>Pickup Location</Popup></Marker>
        <Marker position={routeCoordinates[routeCoordinates.length - 1]} icon={redNeonIcon}><Popup>Destination</Popup></Marker>
        <Polyline positions={routeCoordinates} pathOptions={{ color: "#22d3ee", weight: 14, opacity: 0.25 }} />
        <Polyline positions={routeCoordinates} pathOptions={{ color: "#22d3ee", weight: 6, opacity: 1 }} />
      </MapContainer>
    </motion.div>
  )
}
