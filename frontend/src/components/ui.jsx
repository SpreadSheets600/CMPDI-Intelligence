import { motion } from "framer-motion";

// Page header used by every workspace screen, with the standard rise-in.
export function PageHeader({ title, subtitle, children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="flex flex-wrap items-start justify-between gap-3"
    >
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 max-w-[70ch] text-[15px] text-stone-500">{subtitle}</p>}
      </div>
      {children}
    </motion.div>
  );
}

// Wraps page content in the standard staggered entrance.
export function Rise({ delay = 0, className = "", children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1], delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

export function Loading({ label = "Loading..." }) {
  return (
    <p className="mt-10 animate-pulse text-center text-sm text-stone-500">{label}</p>
  );
}

export function ErrorBox({ message }) {
  return (
    <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13.5px] text-red-700">
      {message}
    </div>
  );
}
