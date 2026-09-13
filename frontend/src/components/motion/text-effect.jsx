import { useMemo } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

const PRESETS = {
  blur: { container: {}, item: { hidden: { opacity: 0, filter: 'blur(12px)' }, show: { opacity: 1, filter: 'blur(0px)' }, exit: { opacity: 0, filter: 'blur(12px)' } } },
  'blur-sm': { container: {}, item: { hidden: { opacity: 0, filter: 'blur(4px)' }, show: { opacity: 1, filter: 'blur(0px)' }, exit: { opacity: 0, filter: 'blur(4px)' } } },
  fade: { container: {}, item: { hidden: { opacity: 0 }, show: { opacity: 1 }, exit: { opacity: 0 } } },
  'fade-in-blur': { container: {}, item: { hidden: { opacity: 0, y: 20, filter: 'blur(8px)' }, show: { opacity: 1, y: 0, filter: 'blur(0px)' }, exit: { opacity: 0, y: 20, filter: 'blur(8px)' } } },
  slide: { container: {}, item: { hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 }, exit: { opacity: 0, y: 20 } } },
  scale: { container: {}, item: { hidden: { opacity: 0, scale: 0.8 }, show: { opacity: 1, scale: 1 }, exit: { opacity: 0, scale: 0.8 } } },
};

export function TextEffect({
  children,
  per = 'word',
  as = 'p',
  variants,
  className,
  preset = 'fade',
  delay = 0,
  trigger = true,
  onAnimationComplete,
  onAnimationStart,
  segmentWrapperClassName,
  style,
  containerTransition,
  segmentTransition,
  speedReveal = 1,
  speedSegment = 1,
}) {
  const segments = useMemo(() => {
    const text = typeof children === 'string' ? children : '';
    if (per === 'line') return text.split('\n');
    if (per === 'char') return text.split('');
    return text.split(/(\s+)/);
  }, [children, per]);

  const base = PRESETS[preset] ?? PRESETS.fade;
  const containerVariants = variants?.container ?? base.container;
  const itemVariants = variants?.item ?? base.item;

  const MOTION_TAG = as === 'h1' ? motion.h1 : as === 'h2' ? motion.h2 : as === 'h3' ? motion.h3 : as === 'span' ? motion.span : as === 'div' ? motion.div : motion.p;

  return (
    <AnimatePresence mode='popLayout'>
      {trigger && (
        <MOTION_TAG
          initial='hidden'
          animate='show'
          exit='exit'
          variants={{
            ...containerVariants,
            show: { transition: { staggerChildren: 0.04 / speedReveal, delayChildren: delay, ...(containerTransition ?? {}) } },
          }}
          onAnimationComplete={onAnimationComplete}
          onAnimationStart={onAnimationStart}
          className={cn(className)}
          style={style}
        >
          {segments.map((segment, i) => (
            <motion.span
              key={`${per}-${i}`}
              variants={itemVariants}
              transition={{ duration: 0.4 / speedSegment, ease: [0.16, 1, 0.3, 1], ...(segmentTransition ?? {}) }}
              className={cn(per === 'line' ? 'block' : 'inline-block whitespace-pre', segmentWrapperClassName)}
              aria-hidden={per !== 'line' ? true : undefined}
            >
              {segment === ' ' || segment === '' ? '\u00A0' : segment}
            </motion.span>
          ))}
        </MOTION_TAG>
      )}
    </AnimatePresence>
  );
}
