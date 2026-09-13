import { motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

const BLUR = { softest: 4, soft: 12, medium: 32, strong: 64, stronger: 96, strongest: 128, none: 0 };

export function GlowEffect({ className, style, colors = ['#FF5733', '#33FF57', '#3357FF', '#F1C40F'], mode = 'rotate', blur = 'medium', transition, scale = 1, duration = 5 }) {
  const blurPx = typeof blur === 'number' ? blur : (BLUR[blur] ?? 32);
  const conic = `conic-gradient(from 0deg, ${colors.join(', ')}, ${colors[0]})`;
  const anim =
    mode === 'static' ? {} :
    mode === 'pulse' ? { opacity: [0.5, 1, 0.5], scale: [scale * 0.98, scale, scale * 0.98] } :
    mode === 'breathe' ? { opacity: [0.6, 1, 0.6], scale: [scale * 0.97, scale * 1.02, scale * 0.97] } :
    mode === 'colorShift' ? { filter: [`hue-rotate(0deg) blur(${blurPx}px)`, `hue-rotate(360deg) blur(${blurPx}px)`] } :
    mode === 'flowHorizontal' ? { backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] } :
    { rotate: [0, 360] };
  return (
    <motion.div
      aria-hidden='true'
      className={cn('pointer-events-none absolute inset-0', className)}
      style={{ background: mode === 'flowHorizontal' ? `linear-gradient(90deg, ${colors.join(', ')})` : conic, filter: mode === 'colorShift' ? undefined : `blur(${blurPx}px)`, scale, ...style }}
      animate={anim}
      transition={transition ?? { duration, repeat: Infinity, ease: 'linear' }}
    />
  );
}
