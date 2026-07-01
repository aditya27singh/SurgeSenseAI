import { motion } from "framer-motion"

export default function HeroSection() {
  return (
    <motion.div initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }} className="text-center mb-16">
      <h2 className="text-4xl md:text-6xl font-extrabold leading-tight mb-6 break-words">
        Real-Time Intelligent<span className="text-cyan-400"> Fare Prediction</span>
      </h2>
      <p className="text-gray-400 text-lg max-w-3xl mx-auto">AI-powered dynamic pricing using live traffic, weather, routing intelligence, and machine learning.</p>
    </motion.div>
  )
}
