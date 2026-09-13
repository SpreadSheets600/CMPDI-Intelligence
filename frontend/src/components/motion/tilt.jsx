import { useRef } from 'react';
import { motion, useMotionValue, useSpring } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function Tilt({ children, className, style, rotationFactor = 15, isRevese = false, springOptions }) {
  const ref = useRef(null);
  const rx = useMotionValue(0);
  const ry = useMotionValue(0);
  const srx = useSpring(rx, springOptions ?? { stiffness: 200, damping: 18 });
  const sry = useSpring(ry, springOptions ?? { stiffness: 200, damping: 18 });
  const dir = isRevese ? -1 : 1;

  const onMove = (e) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width - 0.5;
    const py = (e.clientY - r.top) / r.height - 0.5;
    ry.set(px * rotationFactor * dir);
    rx.set(-py * rotationFactor * dir);
  };
  const reset = () => { rx.set(0); ry.set(0); };

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={reset}
      style={{ rotateX: srx, rotateY: sry, transformPerspective: 900, ...style }}
      className={cn(className)}
    >
      {children}
    </motion.div>
  );
}
