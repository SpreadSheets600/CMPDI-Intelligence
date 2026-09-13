import { motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

const PRESETS = {
  fade: { container: { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }, item: { hidden: { opacity: 0 }, show: { opacity: 1 } } },
  slide: { container: { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }, item: { hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } } },
  scale: { container: { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }, item: { hidden: { opacity: 0, scale: 0.95 }, show: { opacity: 1, scale: 1 } } },
  blur: { container: { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }, item: { hidden: { opacity: 0, filter: 'blur(8px)' }, show: { opacity: 1, filter: 'blur(0px)' } } },
  'blur-sm': { container: { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }, item: { hidden: { opacity: 0, filter: 'blur(4px)' }, show: { opacity: 1, filter: 'blur(0px)' } } },
  'blur-slide': { container: { hidden: {}, show: { transition: { staggerChildren: 0.06 } } }, item: { hidden: { opacity: 0, y: 12, filter: 'blur(6px)' }, show: { opacity: 1, y: 0, filter: 'blur(0px)' } } },
};

export function AnimatedGroup({ children, className, variants, preset, as = 'div', asChild = 'div', ...rest }) {
  const selected = (variants ?? (preset ? PRESETS[preset] : PRESETS['blur-slide']));
  const Container = motion[as] ?? motion.div;
  const Child = motion[asChild] ?? motion.div;
  const items = Array.isArray(children) ? children : [children];
  return (
    <Container initial='hidden' animate='show' variants={selected.container} className={cn(className)} {...rest}>
      {items.map((child, i) => (
        <Child key={i} variants={selected.item} transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}>
          {child}
        </Child>
      ))}
    </Container>
  );
}
