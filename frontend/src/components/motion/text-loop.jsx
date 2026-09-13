import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function TextLoop({ children, className, interval = 2, transition, variants, onIndexChange, trigger = true, mode = 'popLayout' }) {
  const items = Array.isArray(children) ? children : [children];
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!trigger || items.length < 2) return;
    const id = setInterval(() => {
      setIndex((i) => {
        const next = (i + 1) % items.length;
        onIndexChange?.(next);
        return next;
      });
    }, interval * 1000);
    return () => clearInterval(id);
  }, [trigger, interval, items.length]);

  return (
    <span className={cn('relative inline-flex overflow-hidden', className)}>
      <AnimatePresence mode={mode} initial={false}>
        <motion.span
          key={index}
          initial='enter'
          animate='animate'
          exit='exit'
          variants={variants ?? {
            enter: { y: 14, opacity: 0 },
            animate: { y: 0, opacity: 1 },
            exit: { y: -14, opacity: 0 },
          }}
          transition={transition ?? { duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
          className='inline-block whitespace-nowrap'
        >
          {items[index]}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}
