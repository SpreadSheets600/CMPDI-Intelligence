import { createContext, useContext, useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils.js';

const DialogContext = createContext({ open: false, setOpen: () => {} });

export function Dialog({ children, open, defaultOpen = false, onOpenChange, variants, transition, className }) {
  const [internal, setInternal] = useState(defaultOpen);
  const isControlled = open !== undefined;
  const isOpen = isControlled ? open : internal;
  const setOpen = (v) => {
    const next = typeof v === 'function' ? v(isOpen) : v;
    if (!isControlled) setInternal(next);
    onOpenChange?.(next);
  };

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    if (isOpen) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen]);

  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  return (
    <DialogContext.Provider value={{ open: isOpen, setOpen }}>
      <div className={cn(className)}>{children}</div>
    </DialogContext.Provider>
  );
}

export function DialogTrigger({ children, className }) {
  const { setOpen } = useContext(DialogContext);
  return (
    <button type='button' onClick={() => setOpen(true)} className={cn(className)}>
      {children}
    </button>
  );
}

export function DialogContent({ children, className, container }) {
  const { open, setOpen } = useContext(DialogContext);
  return (
    <AnimatePresence>
      {open && (
        <div className='fixed inset-0 z-50 flex items-center justify-center p-4'>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className='absolute inset-0 bg-ink/50 backdrop-blur-sm'
            onClick={() => setOpen(false)}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 12 }}
            transition={{ type: 'spring', bounce: 0.2, duration: 0.5 }}
            role='dialog'
            aria-modal='true'
            className={cn('relative w-full max-w-md rounded-2xl border border-seam bg-white p-6 shadow-lift', className)}
          >
            {children}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}

export function DialogHeader({ children, className }) {
  return <div className={cn('mb-3', className)}>{children}</div>;
}

export function DialogTitle({ children, className }) {
  return <h2 className={cn('text-lg font-semibold tracking-tight', className)}>{children}</h2>;
}

export function DialogDescription({ children, className }) {
  return <p className={cn('mt-1 text-sm text-stone-500', className)}>{children}</p>;
}

export function DialogClose({ children, className, disabled }) {
  const { setOpen } = useContext(DialogContext);
  if (children) {
    return <button type='button' disabled={disabled} onClick={() => setOpen(false)} className={cn(className)}>{children}</button>;
  }
  return (
    <button type='button' disabled={disabled} onClick={() => setOpen(false)} aria-label='Close dialog'
      className={cn('absolute right-4 top-4 rounded-md p-1 text-stone-400 transition-colors hover:bg-paper hover:text-ink', className)}>
      <X className='h-4 w-4' />
    </button>
  );
}
