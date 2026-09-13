import { createContext, useContext, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

const DisclosureContext = createContext({ open: false, toggle: () => {} });

export function Disclosure({ children, open, onOpenChange, className, variants, transition }) {
  const [internal, setInternal] = useState(false);
  const isControlled = open !== undefined;
  const isOpen = isControlled ? open : internal;
  const toggle = () => {
    const next = !isOpen;
    if (!isControlled) setInternal(next);
    onOpenChange?.(next);
  };
  return (
    <DisclosureContext.Provider value={{ open: isOpen, toggle }}>
      <div className={cn(className)}>{children}</div>
    </DisclosureContext.Provider>
  );
}

export function DisclosureTrigger({ children, className }) {
  const { open, toggle } = useContext(DisclosureContext);
  return (
    <button type='button' onClick={toggle} aria-expanded={open} className={cn('flex w-full cursor-pointer items-center justify-between gap-3 text-left', className)}>
      {children}
    </button>
  );
}

export function DisclosureContent({ children, className }) {
  const { open } = useContext(DisclosureContext);
  return (
    <AnimatePresence initial={false}>
      {open && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 260, damping: 30 }}
          className='overflow-hidden'
        >
          <div className={cn(className)}>{children}</div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
