import { AnimatePresence, motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function TransitionPanel({ children, activeIndex, className, transition, variants, ...motionProps }) {
  const panels = Array.isArray(children) ? children : [children];
  const active = panels[activeIndex] ?? null;
  return (
    <div className={cn('relative overflow-hidden', className)}>
      <AnimatePresence mode='popLayout' initial={false}>
        <motion.div
          key={activeIndex}
          initial='enter'
          animate='center'
          exit='exit'
          variants={variants ?? {
            enter: { opacity: 0, x: 24 },
            center: { opacity: 1, x: 0 },
            exit: { opacity: 0, x: -24 },
          }}
          transition={transition ?? { duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
          {...motionProps}
        >
          {active}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
