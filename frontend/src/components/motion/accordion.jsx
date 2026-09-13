import { createContext, useContext, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Plus } from 'lucide-react';
import { cn } from '../../lib/utils.js';

const AccordionContext = createContext({ expanded: null, setExpanded: () => {} });

export function Accordion({ children, className, transition, variants, expandedValue, onValueChange }) {
  const [internal, setInternal] = useState(null);
  const isControlled = expandedValue !== undefined;
  const expanded = isControlled ? expandedValue : internal;
  const setExpanded = (v) => {
    if (!isControlled) setInternal(v);
    onValueChange?.(v);
  };
  return (
    <AccordionContext.Provider value={{ expanded, setExpanded }}>
      <div className={cn('space-y-3', className)}>{children}</div>
    </AccordionContext.Provider>
  );
}

export function AccordionItem({ value, children, className }) {
  const { expanded } = useContext(AccordionContext);
  const isOpen = expanded === value;
  return (
    <div data-expanded={isOpen}
      className={cn('group overflow-hidden rounded-2xl border bg-white transition-colors duration-300', isOpen ? 'border-coalline' : 'border-seam hover:border-coalline', className)}>
      {children}
    </div>
  );
}

export function AccordionTrigger({ children, className }) {
  return (
    <div className={cn(className)}>
      {children}
    </div>
  );
}

export function AccordionHeaderButton({ itemValue, children, className }) {
  const { expanded, setExpanded } = useContext(AccordionContext);
  const isOpen = expanded === itemValue;
  return (
    <button type='button' onClick={() => setExpanded(isOpen ? null : itemValue)} aria-expanded={isOpen}
      className={cn('flex w-full items-center justify-between gap-4 px-6 py-5 text-left', className)}>
      <span className='text-[15px] font-semibold tracking-tight'>{children}</span>
      <span className={cn('flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-seam text-stone-400 transition-all duration-300 group-data-[expanded]:rotate-45', isOpen && 'rotate-45 border-coal text-coal')} aria-hidden='true'>
        <Plus className='h-3.5 w-3.5' />
      </span>
    </button>
  );
}

export function AccordionContent({ children, className }) {
  return (
    <div className={cn('px-6 pb-6 text-[14px] leading-relaxed text-stone-500', className)}>
      {children}
    </div>
  );
}

export function AccordionAnimatedItem({ value, title, children, triggerClassName, contentClassName }) {
  const { expanded, setExpanded } = useContext(AccordionContext);
  const isOpen = expanded === value;
  return (
    <div data-expanded={isOpen} className='group overflow-hidden rounded-2xl border bg-white transition-colors duration-300 data-[expanded=true]:border-coalline data-[expanded=false]:border-seam data-[expanded=false]:hover:border-coalline'>
      <button type='button' onClick={() => setExpanded(isOpen ? null : value)} aria-expanded={isOpen}
        className={cn('flex w-full items-center justify-between gap-4 px-6 py-5 text-left', triggerClassName)}>
        <span className='text-[15px] font-semibold tracking-tight'>{title}</span>
        <span className={cn('flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-seam text-stone-400 transition-all duration-300', isOpen && 'rotate-45 border-coal text-coal')} aria-hidden='true'>
          <Plus className='h-3.5 w-3.5' />
        </span>
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 260, damping: 30 }} className='overflow-hidden'>
            <div className={cn('px-6 pb-6 text-[14px] leading-relaxed text-stone-500', contentClassName)}>{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
