import { useRef, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'motion/react';
import { cn } from '../../lib/utils.js';

const SPRING = { stiffness: 200, damping: 16, mass: 0.2 };

export function Magnetic({ children, className, intensity = 0.6, range = 100, actionArea = 'self', springOptions }) {
  const ref = useRef(null);
  const [hover, setHover] = useState(false);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, springOptions ?? SPRING);
  const sy = useSpring(y, springOptions ?? SPRING);

  const onMove = (e) => {
    const el = actionArea === 'global' ? null : ref.current;
    if (actionArea === 'global') {
      const cx = window.innerWidth / 2, cy = window.innerHeight / 2;
      const dx = e.clientX - cx, dy = e.clientY - cy;
      const d = Math.hypot(dx, dy);
      if (d < range * 3) { x.set((dx / d) * range * intensity * 0.2); y.set((dy / d) * range * intensity * 0.2); }
      return;
    }
    if (!el) return;
    const r = el.getBoundingClientRect();
    const dx = e.clientX - (r.left + r.width / 2);
    const dy = e.clientY - (r.top + r.height / 2);
    const d = Math.hypot(dx, dy);
    if (d < range) { x.set(dx * intensity); y.set(dy * intensity); setHover(true); }
    else { x.set(0); y.set(0); setHover(false); }
  };
  const reset = () => { x.set(0); y.set(0); setHover(false); };

  return (
    <motion.span
      ref={ref}
      onMouseMove={actionArea === 'self' ? onMove : undefined}
      onMouseLeave={reset}
      style={{ x: sx, y: sy, display: 'inline-flex' }}
      className={cn(className)}
    >
      {children}
    </motion.span>
  );
}
