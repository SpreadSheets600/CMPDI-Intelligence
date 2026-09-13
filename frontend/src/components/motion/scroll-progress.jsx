import { motion, useScroll, useSpring } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function ScrollProgress({ className, springOptions, containerRef }) {
  const { scrollYProgress } = useScroll(containerRef ? { container: containerRef } : undefined);
  const scaleX = useSpring(scrollYProgress, springOptions ?? { stiffness: 120, damping: 25, mass: 0.3 });
  return (
    <motion.div
      aria-hidden='true'
      style={{ scaleX }}
      className={cn('fixed inset-x-0 top-0 z-50 h-[3px] origin-left bg-coal', className)}
    />
  );
}
