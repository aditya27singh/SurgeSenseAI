import { useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"

export default function ErrorToast({ message, onClose }) {
  useEffect(() => {
    if (message) {
      const timer = setTimeout(onClose, 5000)
      return () => clearTimeout(timer)
    }
  }, [message, onClose])

  return (
    <AnimatePresence>
      {message && (
        <motion.div initial={{ opacity: 0, y: -50, x: "-50%" }} animate={{ opacity: 1, y: 0, x: "-50%" }} exit={{ opacity: 0, y: -50, x: "-50%" }} className="fixed top-6 left-1/2 z-50 bg-red-500/90 backdrop-blur-xl text-white px-6 py-4 rounded-2xl shadow-2xl border border-red-400/30 max-w-md w-full">
          <div className="flex items-center justify-between gap-4">
            <p className="text-sm font-medium">{message}</p>
            <button onClick={onClose} className="text-white/70 hover:text-white transition text-lg font-bold">✕</button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
