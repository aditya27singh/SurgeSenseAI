import { motion } from "framer-motion"
import { MapPin, Navigation, Sparkles, LocateFixed, MapPinned } from "lucide-react"

export default function PredictionForm({ pickup, setPickup, drop, setDrop, city, setCity, loading, calculateFare, detectLocation }) {
  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }} className="backdrop-blur-xl bg-white/5 border border-white/10 rounded-3xl p-8 shadow-2xl max-w-4xl mx-auto flex flex-col justify-between h-full">
      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Pickup Location</label>
          <div className="flex items-center gap-3 bg-black/30 border border-white/10 rounded-2xl px-4 py-4">
            <MapPin className="text-cyan-400" />
            <input type="text" placeholder="Enter pickup location" value={pickup} onChange={(e) => setPickup(e.target.value)} className="bg-transparent outline-none w-full text-white" />
          </div>
        </div>
        <button onClick={detectLocation} className="mt-3 flex items-center gap-2 text-cyan-400 hover:text-cyan-300 transition text-sm">
          <LocateFixed size={16} /> Use My Current Location
        </button>
        <div>
          <label className="text-sm text-gray-400 mb-2 block">Drop Location</label>
          <div className="flex items-center gap-3 bg-black/30 border border-white/10 rounded-2xl px-4 py-4">
            <Navigation className="text-purple-400" />
            <input type="text" placeholder="Enter destination" value={drop} onChange={(e) => setDrop(e.target.value)} className="bg-transparent outline-none w-full text-white" />
          </div>
        </div>
      </div>
      <div className="grid md:grid-cols-2 gap-6 mt-6">
        <div>
          <label className="text-sm text-gray-400 mb-2 block">City</label>
          <div className="flex items-center gap-3 bg-black/30 border border-white/10 rounded-2xl px-4 py-4">
            <MapPinned className="text-cyan-400" />
            <input type="text" value={city} onChange={(e) => setCity(e.target.value)} placeholder="Enter city" className="bg-transparent outline-none w-full text-white" />
          </div>
        </div>
      </div>
      <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} onClick={calculateFare} className="mt-8 w-full bg-cyan-500 hover:bg-cyan-400 transition text-black font-bold py-4 rounded-2xl flex items-center justify-center gap-2 text-lg">
        {loading ? (
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-black border-t-transparent rounded-full animate-spin" />
            <span>AI Engine Calculating...</span>
          </div>
        ) : (<><Sparkles /> Calculate Intelligent Fare</>)}
      </motion.button>
    </motion.div>
  )
}
