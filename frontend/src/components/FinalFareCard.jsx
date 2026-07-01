import { motion } from "framer-motion"

export default function FinalFareCard({ result }) {
  return (
    <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="flex justify-center items-center px-4">
      <div className="bg-white/5 border border-cyan-500/20 rounded-3xl p-8 max-w-2xl w-full min-w-0 flex flex-col justify-center items-center shadow-[0_0_60px_rgba(34,211,238,0.15)] hover:border-cyan-400/40 hover:scale-[1.02] transition-all duration-300">
        <p className="text-sm text-gray-500 mb-6 text-center">{result.distance_km < 50 ? "Urban AI-weighted pricing model applied" : "Long-distance rule-based pricing applied"}</p>
        <h2 className="text-3xl text-gray-400 mb-6">Final AI Predicted Fare</h2>
        <div className="text-5xl md:text-7xl font-bold text-cyan-400 animate-pulse break-words text-center">₹{result.predicted_fare.toFixed(2)}</div>
      </div>
    </motion.div>
  )
}
