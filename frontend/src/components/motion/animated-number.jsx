import { useEffect, useRef } from 'react';
import { animate, motion, useInView, useMotionValue, useSpring } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function AnimatedNumber({ value, className, springOptions, as = 'span' }) {
  const mv = useMotionValue(0);
  const spring = useSpring(mv, springOptions ?? { bounce: 0, duration: 1200 });
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });

  useEffect(() => {
    if (inView && Number.isFinite(value)) {
      const controls = animate(mv, value, { duration: 1.2, ease: [0.16, 1, 0.3, 1] });
      return controls.stop;
    }
  }, [inView, value]);

  useEffect(() => {
    const unsub = spring.on('change', (v) => {
      if (ref.current) ref.current.textContent = Math.round(v).toLocaleString('en-IN');
    });
    return unsub;
  }, [spring]);

  const Tag = motion[as] ?? motion.span;
  return <Tag ref={ref} className={cn('tabular-nums', className)}>0</Tag>;
}
