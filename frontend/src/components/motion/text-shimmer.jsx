import { motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function TextShimmer({ children, as = 'p', className, duration = 2, spread = 2 }) {
  const Tag = motion[as] ?? motion.p;
  return (
    <Tag
      className={cn('bg-clip-text text-transparent', className)}
      style={{
        backgroundImage: 'linear-gradient(110deg, rgb(var(--c-muted1)) 30%, rgb(var(--c-ink)) 50%, rgb(var(--c-muted1)) 70%)',
        backgroundSize: '200% 100%',
      }}
      animate={{ backgroundPositionX: ['200%', '-200%'] }}
      transition={{ duration, repeat: Infinity, ease: 'linear' }}
    >
      {children}
    </Tag>
  );
}
