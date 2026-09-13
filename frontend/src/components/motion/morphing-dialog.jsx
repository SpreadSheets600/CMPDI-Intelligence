import { createContext, useContext, useEffect, useId, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils.js';

const Ctx = createContext(null);

export function MorphingDialog({ children, transition }) {
  const [open, setOpen] = useState(false);
  const layoutId = useId();
  return (
    <Ctx.Provider value={{ open, setOpen, layoutId, transition }}>
      {children}
    </Ctx.Provider>
  );
}

export function MorphingDialogTrigger({ children, className, style, triggerRef }) {
  const { setOpen, layoutId, transition } = useContext(Ctx);
  return (
    <motion.button
      ref={triggerRef}
      layoutId={`morph-dialog-${layoutId}`}
      transition={transition ?? { type: 'spring', bounce: 0.1, duration: 0.5 }}
      type='button'
      onClick={() => setOpen(true)}
      className={cn(className)}
      style={style}
    >
      {children}
    </motion.button>
  );
}

export function MorphingDialogContent({ children, className, style }) {
  const { open, setOpen, layoutId, transition } = useContext(Ctx);
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    if (open) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, setOpen]);
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [open ]);
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className='fixed inset-0 z-50 flex items-center justify-center bg-ink/50 p-4 backdrop-blur-sm'
          onClick={() => setOpen(false)}
        >
          <motion.div
            layoutId={`morph-dialog-${layoutId}`}
            transition={transition ?? { type: 'spring', bounce: 0.1, duration: 0.5 }}
            onClick={(e) => e.stopPropagation()}
            role='dialog'
            aria-modal='true'
            style={style}
            className={cn('relative max-h-[90dvh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-seam bg-white p-6 shadow-lift', className)}
          >
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function MorphingDialogTitle({ children, className, style }) {
  return <h2 className={cn('text-lg font-semibold tracking-tight', className)} style={style}>{children}</h2>;
}

export function MorphingDialogSubtitle({ children, className, style }) {
  return <p className={cn('mt-0.5 text-sm text-stone-500', className)} style={style}>{children}</p>;
}

export function MorphingDialogDescription({ children, className, disableLayoutAnimation, variants }) {
  return <motion.div layout={!disableLayoutAnimation} variants={variants} className={cn('mt-3 text-sm leading-relaxed text-stone-600', className)}>{children}</motion.div>;
}

export function MorphingDialogImage({ src, alt, className, style }) {
  return <img src={src} alt={alt} className={cn('w-full rounded-xl border border-seam object-cover', className)} style={style} />;
}

export function MorphingDialogClose({ children, className, variants }) {
  const { setOpen } = useContext(Ctx);
  if (children) {
    return <button type='button' onClick={() => setOpen(false)} className={cn(className)}>{children}</button>;
  }
  return (
    <motion.button type='button' variants={variants} onClick={() => setOpen(false)} aria-label='Close dialog'
      className={cn('absolute right-4 top-4 rounded-md p-1 text-stone-400 transition-colors hover:bg-paper hover:text-ink', className)}>
      <X className='h-4 w-4' />
    </motion.button>
  );
}
