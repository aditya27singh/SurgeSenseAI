export default function FareBreakdown({ result }) {
  return (
    <div className="bg-gradient-to-br from-red-500/10 to-cyan-500/10 border border-white/10 rounded-3xl p-8 shadow-[0_0_40px_rgba(255,0,80,0.08)] hover:border-red-400/30 hover:scale-[1.01] transition-all duration-300">
      <h2 className="text-4xl font-bold mb-10 text-red-400">AI Fare Breakdown</h2>
      <div className="space-y-8">
        <div className="flex justify-between text-2xl"><span className="text-gray-400">Base Fare</span><span>₹{result.base_fare}</span></div>
        <div className="flex justify-between text-2xl"><span className="text-gray-400">Traffic Surge</span><span className="text-red-400">+₹{result.traffic_surge}</span></div>
        <div className="flex justify-between text-2xl"><span className="text-gray-400">Weather Impact</span><span className="text-yellow-400">+₹{result.weather_surge}</span></div>
        <div className="flex justify-between text-2xl"><span className="text-gray-400">Peak Hour Surge</span><span className="text-cyan-400">+₹{result.peak_hour_surge}</span></div>
      </div>
    </div>
  )
}
