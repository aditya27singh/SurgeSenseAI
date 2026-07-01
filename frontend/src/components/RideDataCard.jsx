import { motion } from "framer-motion"

export default function RideDataCard({ result }) {
  return (
    <motion.div initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} className="bg-white/5 border border-white/10 rounded-3xl p-8 h-fit shadow-[0_0_40px_rgba(34,211,238,0.08)] hover:border-cyan-400/30 hover:scale-[1.01] transition-all duration-300">
      <h2 className="text-4xl font-bold mb-10 text-cyan-400">Ride Data</h2>
      <div className="space-y-8">
        <div className="flex justify-between items-center"><span className="text-gray-400 text-xl">Distance</span><span className="text-3xl font-semibold">{result.distance_km.toFixed(2)} km</span></div>
        <div className="flex justify-between items-center"><span className="text-gray-400 text-xl">ETA</span><span className="text-3xl font-semibold">{result.estimated_duration_minutes.toFixed(0)} min</span></div>
        <div className="flex justify-between items-center"><span className="text-gray-400 text-xl">Weather</span><span className="text-3xl font-semibold capitalize">{result.weather}</span></div>
        <div className="flex justify-between items-center"><span className="text-gray-400 text-xl">Traffic</span>
          <span className={`text-xl font-bold px-5 py-2 rounded-full ${result.traffic === "low" ? "bg-green-500/20 text-green-400" : result.traffic === "medium" ? "bg-yellow-500/20 text-yellow-400" : "bg-red-500/20 text-red-400"}`}>{result.traffic.toUpperCase()}</span>
        </div>
      </div>
    </motion.div>
  )
}
