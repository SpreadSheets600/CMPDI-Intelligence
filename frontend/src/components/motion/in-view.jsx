import { useRef } from 'react';
import { motion, useInView } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function InView({ children, variants, transition, viewOptions, as = 'div', className, once = true }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once, margin: '0px 0px -12% 0px', ...(viewOptions ?? {}) });
  const Tag = motion[as] ?? motion.div;
  return (
    <Tag
      ref={ref}
      initial='hidden'
      animate={inView ? 'visible' : 'hidden'}
      variants={variants ?? { hidden: { opacity: 0, y: 24 }, visible: { opacity: 1, y: 0 } }}
      transition={transition ?? { duration: 0.65, ease: [0.16, 1, 0.3, 1] }}
      className={cn(className)}
    >
      {children}
    </Tag>
  );
}
