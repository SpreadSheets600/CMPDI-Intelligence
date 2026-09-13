import { AnimatePresence, motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

function Digit({ d }) {
  return (
    <span className='relative inline-flex h-[1em] w-[0.62em] items-center justify-center overflow-hidden leading-none'>
      <AnimatePresence mode='popLayout' initial={false}>
        <motion.span
          key={d}
          initial={{ y: '0.9em', opacity: 0 }}
          animate={{ y: '0em', opacity: 1 }}
          exit={{ y: '-0.9em', opacity: 0 }}
          transition={{ type: 'spring', bounce: 0.15, duration: 0.5 }}
          className='inline-block tabular-nums'
        >
          {d}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

export function SlidingNumber({ value, padStart = false, decimalSeparator = '.', className }) {
  let str = String(value ?? '');
  if (padStart) {
    const [int, ...rest] = str.split('.');
    str = (int.length < 2 ? '0' + int : int) + (rest.length ? decimalSeparator + rest.join(decimalSeparator) : '');
  }
  return (
    <span className={cn('inline-flex items-baseline tabular-nums', className)} aria-label={str}>
      {str.split('').map((ch, i) =>
        /[0-9]/.test(ch) ? <Digit key={i} d={ch} /> : <span key={i} className='inline-block'>{ch}</span>
      )}
    </span>
  );
}
