import { useState, useEffect } from "react"
import L from "leaflet"
import { MapContainer, TileLayer, Polyline, useMap, Marker, Popup } from "react-leaflet"
import polyline from "@mapbox/polyline"
import axios from "axios"
import { motion } from "framer-motion"
import {
  MapPin,
  Navigation,
  Sparkles,
  Cloud,
  Timer,
  LocateFixed,
  MapPinned
} from "lucide-react"

function FitBounds({coordinates}) {

  const map = useMap()

  map.flyToBounds(coordinates, {
    padding: [80, 80],
    duration: 2
  })

  return null
}

const redNeonIcon = new L.DivIcon({
  className: "",
  html: `
    <div style="
      width:18px;
      height:18px;
      background:#ff0033;
      border-radius:999px;
      box-shadow:0 0 20px #ff0033;
      border:2px solid white;
    "></div>
  `,
  iconSize: [18, 18]
})

function App() {

  const [pickup, setPickup] = useState("")
  const [drop, setDrop] = useState("")
  const [city, setCity] = useState("")

  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [rideHistory, setRideHistory] = useState([])

  const API_URL= import.meta.env.VITE_API_URL || "http://127.0.1:8000"
  const routeCoordinates = result?.geometry
  ? polyline.decode(result.geometry)
  : []
  const detectLocation = () => {

  navigator.geolocation.getCurrentPosition(

    async (position) => {

      const lat = position.coords.latitude
      const lon = position.coords.longitude

      try {

        const response = await axios.get(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`
        )

        const address = response.data.display_name

        setPickup(address)

      } catch (error) {

        console.error(error)
        alert("Failed to fetch location.")

      }
    },

    () => {

      alert("Location access denied.")

    }

  )
}

  const calculateFare = async () => {

    try {

      setLoading(true)

      const response = await axios.post(
  `${API_URL}/predict`,
  {
    pickup,
    drop,
    city,
    hour: new Date().getHours()
  }
)
      if (response.data.error) {
        alert(response.data.error)
        return
      }

      setResult(response.data)

    } catch (error) {

      console.error(error)
      alert("Prediction failed.")

    } finally {

      setLoading(false)

    }
  }

useEffect(() => {

  const fetchRideHistory = async () => {

    try {

      const response = await fetch(
        `${API_URL}/ride-history`
      )

      const data = await response.json()

      setRideHistory(data)

    } catch (error) {

      console.error("Failed to fetch ride history:", error)

    }

  }

  fetchRideHistory()

}, [result])
const particles = Array.from({ length: 25 }, () => ({
  top: Math.random() * 100,
  left: Math.random() * 100,
  duration: 2 + Math.random() * 4
}))

  return (
    <div className="min-h-screen bg-[#050816] text-white overflow-x-hidden">

      {/* Background Glow */}
      <div className="absolute top-[-100px] left-[-100px] w-[300px] h-[300px] bg-cyan-500 opacity-20 blur-[120px] rounded-full"></div>

      <div className="absolute bottom-[-100px] right-[-100px] w-[300px] h-[300px] bg-purple-500 opacity-20 blur-[120px] rounded-full"></div>

      {/* Cyber Grid */}
<div
  className="fixed inset-0 opacity-[0.07]"
  style={{
    backgroundImage: `
      linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
    `,
    backgroundSize: "40px 40px"
  }}
/>

      {/* Floating Particles */}
<div className="fixed inset-0 overflow-hidden pointer-events-none">

  {particles.map((particle, i) => (

    <div
      key={i}
      className="absolute w-1 h-1 bg-cyan-400 rounded-full opacity-30 animate-[floatParticle_8s_linear_infinite]"
      style={{
        top: `${particle.top}%`,
        left: `${particle.left}%`,
        animationDuration: `${particle.duration}s`
      }}
    />

  ))}

</div>

      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-cyan-500/10 blur-[140px] rounded-full" />

      <div className="relative z-10 w-full px-4 md:px-6 py-10 overflow-x-hidden">

      <div className="max-w-[1600px] mx-auto flex gap-6">

        {/* Sidebar */}
<div className="hidden lg:flex flex-col w-[320px] h-fit
bg-white/5 border border-white/10 rounded-3xl p-6
backdrop-blur-xl sticky top-6">

  <h2 className="text-2xl font-bold text-cyan-400 mb-10">
    AI Command Center
  </h2>

  {/* Navigation */}
  <div className="space-y-4">

    <div className="bg-cyan-500/10 border border-cyan-400/20
    rounded-2xl p-4">

      <p className="text-gray-400 text-sm">
        Predictions
      </p>

      <h3 className="text-3xl font-bold mt-2">
        {rideHistory.length} Rides
      </h3>

    </div>

    <div className="bg-white/5 border border-white/10
    rounded-2xl p-4">

      <p className="text-gray-400 text-sm">
        Avg Fare
      </p>

      <h3 className="text-3xl font-bold mt-2 text-cyan-400">
        ₹{rideHistory.length > 0 ? (rideHistory.reduce((sum, ride) => sum + ride.fare, 0) / rideHistory.length).toFixed(2) : "0.00"}
      </h3>

    </div>

    <div className="bg-white/5 border border-white/10
    rounded-2xl p-4">

      <p className="text-gray-400 text-sm">
        Most Common Traffic
      </p>

      <h3 className="text-2xl font-bold mt-2 text-red-400">
        {rideHistory.length > 0
  ? rideHistory[0].traffic.toUpperCase()
  : "N/A"}
      </h3>

    </div>

  </div>

  {/* Recent Rides */}
  <div className="mt-10">

    <h3 className="text-xl font-bold mb-5 text-white">
      Recent Rides
    </h3>

<div className="space-y-4">

  {rideHistory.map((ride, index) => (

    <div
      key={index}
      className="bg-white/5 rounded-2xl p-4 border border-white/10"
    >

      <p className="font-semibold truncate">
        {ride.pickup} → {ride.drop}
      </p>

      <p className="text-sm text-cyan-400 mt-1">
        ₹{ride.fare.toFixed(2)}
      </p>

      <p className="text-xs text-gray-500 mt-2">
        {ride.traffic.toUpperCase()} • {ride.weather}
      </p>

    </div>

  ))}

</div>

  </div>

</div>

        <div className="flex-1 min-w-0">

        {/* Navbar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-16">
          <h1 className="text-3xl font-bold tracking-wide">
            SurgeSense AI 🚖
          </h1>

          <button className="px-5 py-2 rounded-xl bg-cyan-500/20 border border-cyan-400 hover:bg-cyan-500/30 transition">
            AI Pricing Engine
          </button>
        </div>

        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-6xl font-extrabold leading-tight mb-6 break-words">
            Real-Time Intelligent
            <span className="text-cyan-400"> Fare Prediction</span>
          </h2>

          <p className="text-gray-400 text-lg max-w-3xl mx-auto">
            AI-powered dynamic pricing using live traffic,
            weather, routing intelligence, and machine learning.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-6 items-start">

        {/* Main Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-8 shadow-2xl max-w-4xl mx-auto flex flex-col justify-between h-full"
        >

          <div className="grid md:grid-cols-2 gap-6">

            {/* Pickup */}
            <div>
              <label className="text-sm text-gray-400 mb-2 block">
                Pickup Location
              </label>

              <div className="flex items-center gap-3 bg-black/30 border border-white/10 rounded-2xl px-4 py-4">
                <MapPin className="text-cyan-400" />

                <input
                  type="text"
                  placeholder="Enter pickup location"
                  value={pickup}
                  onChange={(e) => setPickup(e.target.value)}
                  className="bg-transparent outline-none w-full text-white"
                />
              </div>
            </div>

            <button
  onClick={detectLocation}
  className="mt-3 flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition text-sm"
>
  <LocateFixed size={16} />
  Use My Current Location
</button>

            {/* Drop */}
            <div>
              <label className="text-sm text-gray-400 mb-2 block">
                Drop Location
              </label>

              <div className="flex items-center gap-3 bg-black/30 border border-white/10 rounded-2xl px-4 py-4">
                <Navigation className="text-purple-400" />

                <input
                  type="text"
                  placeholder="Enter destination"
                  value={drop}
                  onChange={(e) => setDrop(e.target.value)}
                  className="bg-transparent outline-none w-full text-white"
                />
              </div>
            </div>

          </div>

          {/* Bottom Row */}
          <div className="grid md:grid-cols-2 gap-6 mt-6">

{/* City */}
<div>

  <label className="text-sm text-gray-400 mb-2 block">
    City
  </label>

  <div className="flex items-center gap-3 bg-black/30 border border-white/10 rounded-2xl px-4 py-4">

    <MapPinned className="text-cyan-400" />

    <input
      type="text"
      value={city}
      onChange={(e) => setCity(e.target.value)}
      placeholder="Enter city"
      className="bg-transparent outline-none w-full text-white"
    />

  </div>

</div>
          </div>

          {/* Button */}
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={calculateFare}
            className="mt-8 w-full bg-cyan-500 hover:bg-cyan-400 transition text-black font-bold py-4 rounded-2xl flex items-center justify-center gap-2 text-lg"
          >

            {loading ? (
  <div className="flex items-center gap-3">

    <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin"></div>

    <span>
      AI Engine Calculating...
    </span>

  </div>
) : (
  <>
    <Sparkles />
    Calculate Intelligent Fare
  </>
)}

          </motion.button>

        </motion.div>

        {/* Live Map */}
{result && (

  <motion.div
    initial={{ opacity: 0, x: 30 }}
    animate={{ opacity: 1, x: 0 }}
    className="rounded-3xl overflow-hidden border border-white/10"
  >

    <MapContainer
      center={routeCoordinates[0]}
      zoom={13}
      scrollWheelZoom={false}
      className="h-[500px] w-full"
    >

      <FitBounds coordinates={routeCoordinates} />

      <TileLayer
        attribution='&copy; OpenStreetMap & CartoDB'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />

      {/* Pickup Marker */}
      <Marker position={routeCoordinates[0]}
        icon={redNeonIcon}>
        <Popup>
          Pickup Location
        </Popup>
      </Marker>

      {/* Drop Marker */}
      <Marker position={routeCoordinates[routeCoordinates.length - 1]}
        icon={redNeonIcon}>
        <Popup>
          Destination
        </Popup>
      </Marker>

{/* Glow Layer */}
<Polyline
  positions={routeCoordinates}
  pathOptions={{
    color: "#22d3ee",
    weight: 14,
    opacity: 0.25
  }}
/>

{/* Main Route */}
<Polyline
  positions={routeCoordinates}
  pathOptions={{
    color: "#22d3ee",
    weight: 6,
    opacity: 1
  }}
/>

    </MapContainer>

  </motion.div>
)}

</div>

        {/* Main Dashboard */}
{result && (

  <div className="max-w-7xl mx-auto mt-10 space-y-6">

    {/* Top Row */}
    <div className="grid lg:grid-cols-2 gap-6">

      {/* Ride Data */}
      <motion.div
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        className="bg-white/5 border border-white/10 rounded-3xl p-8 h-fit
shadow-[0_0_40px_rgba(34,211,238,0.08)]
hover:border-cyan-400/30
hover:scale-[1.01]
transition-all duration-300"

      >

        <h2 className="text-4xl font-bold mb-10 text-cyan-400">
          Ride Data
        </h2>

        <div className="space-y-8">


          <div className="flex justify-between items-center">

            <span className="text-gray-400 text-xl">
              Distance
            </span>

            <span className="text-3xl font-semibold">
              {result.distance_km.toFixed(2)} km
            </span>

          </div>

          <div className="flex justify-between items-center">

            <span className="text-gray-400 text-xl">
              ETA
            </span>

            <span className="text-3xl font-semibold">
              {result.estimated_duration_minutes.toFixed(0)} min
            </span>

          </div>

          <div className="flex justify-between items-center">

            <span className="text-gray-400 text-xl">
              Weather
            </span>

            <span className="text-3xl font-semibold capitalize">
              {result.weather}
            </span>

          </div>

          <div className="flex justify-between items-center">

            <span className="text-gray-400 text-xl">
              Traffic
            </span>

            <span
              className={`text-xl font-bold px-5 py-2 rounded-full
              ${
                result.traffic === "low"
                  ? "bg-green-500/20 text-green-400"

                  : result.traffic === "medium"
                  ? "bg-yellow-500/20 text-yellow-400"

                  : "bg-red-500/20 text-red-400"
              }`}
            >
              {result.traffic.toUpperCase()}
            </span>

          </div>

        </div>

      </motion.div>

     {/* AI Breakdown */}
      <div className="bg-gradient-to-br from-red-500/10 to-cyan-500/10
border border-white/10 rounded-3xl p-8
shadow-[0_0_40px_rgba(255,0,80,0.08)]
hover:border-red-400/30
hover:scale-[1.01]
transition-all duration-300"
      >


        <h2 className="text-4xl font-bold mb-10 text-red-400">
          AI Fare Breakdown
        </h2>

        <div className="space-y-8">

          <div className="flex justify-between text-2xl">
            <span className="text-gray-400">
              Base Fare
            </span>

            <span>
              ₹{result.base_fare}
            </span>
          </div>

          <div className="flex justify-between text-2xl">
            <span className="text-gray-400">
              Traffic Surge
            </span>

            <span className="text-red-400">
              +₹{result.traffic_surge}
            </span>
          </div>

          <div className="flex justify-between text-2xl">
            <span className="text-gray-400">
              Weather Impact
            </span>

            <span className="text-yellow-400">
              +₹{result.weather_surge}
            </span>
          </div>

          <div className="flex justify-between text-2xl">
            <span className="text-gray-400">
              Peak Hour Surge
            </span>

            <span className="text-cyan-400">
              +₹{result.peak_hour_surge}
            </span>
          </div>

        </div>

      </div>
    </div>

    {/* Bottom Row */}
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-center items-center px-4"
    >

      {/* Final Fare Card */}
      <div className="bg-white/5 border border-cyan-500/20 rounded-3xl p-8
max-w-2xl w-full min-w-0
flex flex-col justify-center items-center
shadow-[0_0_60px_rgba(34,211,238,0.15)]
hover:border-cyan-400/40
hover:scale-[1.02]
transition-all duration-300">


                <p className="text-sm text-gray-500 mb-6 text-center">

  {result.distance_km < 50

    ? "Urban AI-weighted pricing model applied"

    : "Long-distance rule-based pricing applied"}

</p>
        <h2 className="text-3xl text-gray-400 mb-6">
          Final AI Predicted Fare
        </h2>

        <div className="text-5xl md:text-7xl font-bold text-cyan-400 animate-pulse break-words text-center">
          ₹{result.predicted_fare.toFixed(2)}
        </div>

      </div>

    </motion.div>

  </div>
)}
        </div>
      </div>
      </div>
    </div>
  )
}

export default App