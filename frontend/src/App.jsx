import { useState, useEffect, useCallback } from "react"
import polyline from "@mapbox/polyline"
import axios from "axios"

import BackgroundEffects from "./components/BackgroundEffects"
import Navbar from "./components/Navbar"
import HeroSection from "./components/HeroSection"
import PredictionForm from "./components/PredictionForm"
import RouteMap from "./components/RouteMap"
import RideDataCard from "./components/RideDataCard"
import FareBreakdown from "./components/FareBreakdown"
import FinalFareCard from "./components/FinalFareCard"
import Sidebar from "./components/Sidebar"
import ErrorToast from "./components/ErrorToast"

function App() {
  const [pickup, setPickup] = useState("")
  const [drop, setDrop] = useState("")
  const [city, setCity] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [rideHistory, setRideHistory] = useState([])
  const [error, setError] = useState(null)

  const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

  const routeCoordinates = result?.geometry ? polyline.decode(result.geometry) : []

  const detectLocation = useCallback(() => {
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const { latitude: lat, longitude: lon } = position.coords
        try {
          const response = await axios.get(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`)
          setPickup(response.data.display_name)
        } catch { setError("Failed to fetch location.") }
      },
      () => setError("Location access denied.")
    )
  }, [])

  const calculateFare = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axios.post(`${API_URL}/predict`, { pickup, drop, city, hour: new Date().getHours() })
      if (response.data.error) { setError(response.data.error); return }
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || "Prediction failed. Please try again.")
    } finally { setLoading(false) }
  }, [API_URL, pickup, drop, city])

  useEffect(() => {
    const fetchRideHistory = async () => {
      try {
        const response = await fetch(`${API_URL}/ride-history`)
        const data = await response.json()
        setRideHistory(data)
      } catch { console.error("Failed to fetch ride history") }
    }
    fetchRideHistory()
  }, [result, API_URL])

  return (
    <div className="min-h-screen bg-[#050816] text-white overflow-x-hidden">
      <BackgroundEffects />
      <ErrorToast message={error} onClose={() => setError(null)} />
      <div className="relative z-10 w-full px-4 md:px-6 py-10 overflow-x-hidden">
        <div className="max-w-[1600px] mx-auto flex gap-6">
          <Sidebar rideHistory={rideHistory} />
          <div className="flex-1 min-w-0">
            <Navbar />
            <HeroSection />
            <div className="grid lg:grid-cols-2 gap-6 items-start">
              <PredictionForm pickup={pickup} setPickup={setPickup} drop={drop} setDrop={setDrop} city={city} setCity={setCity} loading={loading} calculateFare={calculateFare} detectLocation={detectLocation} />
              {result && <RouteMap routeCoordinates={routeCoordinates} />}
            </div>
            {result && (
              <div className="max-w-7xl mx-auto mt-10 space-y-6">
                <div className="grid lg:grid-cols-2 gap-6">
                  <RideDataCard result={result} />
                  <FareBreakdown result={result} />
                </div>
                <FinalFareCard result={result} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App