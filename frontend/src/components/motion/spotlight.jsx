import { useRef } from 'react';
import { motion, useMotionTemplate, useMotionValue, useSpring } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function Spotlight({ children, className, size = 200, springOptions }) {
  const ref = useRef(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const sx = useSpring(x, springOptions ?? { bounce: 0 });
  const sy = useSpring(y, springOptions ?? { bounce: 0 });
  const bg = useMotionTemplate`radial-gradient(${size}px circle at ${sx}px ${sy}px, rgb(var(--c-coal) / 0.12), transparent 70%)`;

  return (
    <div
      ref={ref}
      onMouseMove={(e) => {
        const r = ref.current?.getBoundingClientRect();
        if (!r) return;
        x.set(e.clientX - r.left);
        y.set(e.clientY - r.top);
      }}
      className={cn('group/spotlight relative overflow-hidden', className)}
    >
      <motion.div className='pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover/spotlight:opacity-100' style={{ background: bg }} aria-hidden='true' />
      {children}
    </div>
  );
}
