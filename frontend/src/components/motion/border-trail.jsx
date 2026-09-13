import { motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function BorderTrail({ className, size = 60, transition, onAnimationComplete }) {
  return (
    <span className='pointer-events-none absolute inset-0 z-0 overflow-hidden rounded-[inherit]' aria-hidden='true'>
      <motion.span
        className={cn('absolute left-0 top-0 bg-coal', className)}
        style={{ width: size, height: 2, offsetPath: `rect(0 auto auto 0 round ${size}px)`, offsetRotate: '0deg' }}
        animate={{ offsetDistance: ['0%', '100%'] }}
        transition={transition ?? { duration: 3, repeat: Infinity, ease: 'linear' }}
        onAnimationComplete={onAnimationComplete}
      />
    </span>
  );
}
