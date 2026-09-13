import { createContext, useContext, useEffect, useId, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { cn } from '../../lib/utils.js';
import { useClickOutside } from '../../hooks/useClickOutside.js';

const Ctx = createContext(null);

export function MorphingPopover({ children, transition, defaultOpen = false, open, onOpenChange, variants, className }) {
  const [internal, setInternal] = useState(defaultOpen);
  const isControlled = open !== undefined;
  const isOpen = isControlled ? open : internal;
  const layoutId = useId();
  const ref = useRef(null);

  const setIsOpen = (v) => {
    const next = typeof v === 'function' ? v(isOpen) : v;
    if (!isControlled) setInternal(next);
    onOpenChange?.(next);
  };

  useClickOutside(ref, () => isOpen && setIsOpen(false));

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setIsOpen(false); };
    if (isOpen) window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [isOpen]);

  return (
    <Ctx.Provider value={{ open: isOpen, setOpen: setIsOpen, layoutId, transition, variants }}>
      <div ref={ref} className={cn('relative inline-block', className)}>{children}</div>
    </Ctx.Provider>
  );
}

export function MorphingPopoverTrigger({ children, asChild = false, className }) {
  const { setOpen, layoutId, transition } = useContext(Ctx);
  if (asChild) {
    return (
      <motion.span layoutId={`morph-popover-${layoutId}`} transition={transition ?? { type: 'spring', bounce: 0.1, duration: 0.4 }}
        onClick={() => setOpen(true)} className={cn('inline-block cursor-pointer', className)}>
        {children}
      </motion.span>
    );
  }
  return (
    <motion.button layoutId={`morph-popover-${layoutId}`} transition={transition ?? { type: 'spring', bounce: 0.1, duration: 0.4 }}
      type='button' onClick={() => setOpen(true)} className={cn(className)}>
      {children}
    </motion.button>
  );
}

export function MorphingPopoverContent({ children, className }) {
  const { open, layoutId, transition, variants } = useContext(Ctx);
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          layoutId={`morph-popover-${layoutId}`}
          transition={transition ?? { type: 'spring', bounce: 0.1, duration: 0.4 }}
          variants={variants}
          initial='hidden'
          animate='visible'
          exit='hidden'
          role='dialog'
          className={cn('absolute z-40 mt-2 w-72 rounded-xl border border-seam bg-white p-4 shadow-lift', className)}
        >
          {children}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
