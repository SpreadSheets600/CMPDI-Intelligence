import { motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function InfiniteSlider({ children, gap = 16, speed = 100, speedOnHover, direction = 'horizontal', reverse = false, className }) {
  const horizontal = direction === 'horizontal';
  const duration = 2000 / Math.max(speed, 1);
  return (
    <div className={cn('overflow-hidden', className)} aria-hidden='true'>
      <motion.div
        className='flex w-max'
        style={horizontal ? { gap, flexDirection: 'row' } : { gap, flexDirection: 'column' }}
        animate={horizontal ? { x: reverse ? ['-50%', '0%'] : ['0%', '-50%'] } : { y: reverse ? ['-50%', '0%'] : ['0%', '-50%'] }}
        transition={{ duration: duration * 10, repeat: Infinity, ease: 'linear' }}
      >
        {children}
        {children}
      </motion.div>
    </div>
  );
}
