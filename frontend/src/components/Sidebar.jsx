export default function Sidebar({ rideHistory }) {
  return (
    <div className="hidden lg:flex flex-col w-[320px] h-fit bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-xl sticky top-6">
      <h2 className="text-2xl font-bold text-cyan-400 mb-10">AI Command Center</h2>
      <div className="space-y-4">
        <div className="bg-cyan-500/10 border border-cyan-400/20 rounded-2xl p-4">
          <p className="text-gray-400 text-sm">Predictions</p>
          <h3 className="text-3xl font-bold mt-2">{rideHistory.length} Rides</h3>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
          <p className="text-gray-400 text-sm">Avg Fare</p>
          <h3 className="text-3xl font-bold mt-2 text-cyan-400">₹{rideHistory.length > 0 ? (rideHistory.reduce((sum, ride) => sum + ride.fare, 0) / rideHistory.length).toFixed(2) : "0.00"}</h3>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-2xl p-4">
          <p className="text-gray-400 text-sm">Most Common Traffic</p>
          <h3 className="text-2xl font-bold mt-2 text-red-400">{rideHistory.length > 0 ? rideHistory[0].traffic.toUpperCase() : "N/A"}</h3>
        </div>
      </div>
      <div className="mt-10">
        <h3 className="text-xl font-bold mb-5 text-white">Recent Rides</h3>
        <div className="space-y-4">
          {rideHistory.map((ride, index) => (
            <div key={index} className="bg-white/5 rounded-2xl p-4 border border-white/10">
              <p className="font-semibold truncate">{ride.pickup} → {ride.drop}</p>
              <p className="text-sm text-cyan-400 mt-1">₹{ride.fare.toFixed(2)}</p>
              <p className="text-xs text-gray-500 mt-2">{ride.traffic.toUpperCase()} • {ride.weather}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
