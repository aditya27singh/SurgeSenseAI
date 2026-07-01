import { useMemo } from "react"

export default function BackgroundEffects() {
  const particles = useMemo(
    () => Array.from({ length: 25 }, () => ({
      top: Math.random() * 100,
      left: Math.random() * 100,
      duration: 2 + Math.random() * 4,
    })),
    []
  )

  return (
    <>
      <div className="absolute top-[-100px] left-[-100px] w-[300px] h-[300px] bg-cyan-500 opacity-20 blur-[120px] rounded-full" />
      <div className="absolute bottom-[-100px] right-[-100px] w-[300px] h-[300px] bg-purple-500 opacity-20 blur-[120px] rounded-full" />
      <div className="fixed inset-0 opacity-[0.07]" style={{ backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`, backgroundSize: "40px 40px" }} />
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {particles.map((particle, i) => (
          <div key={i} className="absolute w-1 h-1 bg-cyan-400 rounded-full opacity-30 animate-[floatParticle_8s_linear_infinite]" style={{ top: `${particle.top}%`, left: `${particle.left}%`, animationDuration: `${particle.duration}s` }} />
        ))}
      </div>
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-cyan-500/10 blur-[140px] rounded-full" />
    </>
  )
}
