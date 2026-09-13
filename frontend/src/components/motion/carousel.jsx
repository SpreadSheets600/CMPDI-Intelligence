import { Children, createContext, useContext, useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { cn } from '../../lib/utils.js';

const CarouselContext = createContext({ index: 0, setIndex: () => {}, itemsCount: 0, setItemsCount: () => {}, disableDrag: false });
export const useCarousel = () => useContext(CarouselContext);

export function Carousel({ children, className, initialIndex = 0, index, onIndexChange, disableDrag = false }) {
  const [internal, setInternal] = useState(initialIndex);
  const [itemsCount, setItemsCount] = useState(0);
  const isControlled = index !== undefined;
  const current = isControlled ? index : internal;
  const setIndex = (v) => {
    const next = typeof v === 'function' ? v(current) : v;
    if (!isControlled) setInternal(next);
    onIndexChange?.(next);
  };
  return (
    <CarouselContext.Provider value={{ index: current, setIndex, itemsCount, setItemsCount, disableDrag }}>
      <div className={cn('relative overflow-hidden', className)}>{children}</div>
    </CarouselContext.Provider>
  );
}

export function CarouselContent({ children, className, transition }) {
  const { index, setItemsCount, disableDrag } = useContext(CarouselContext);
  const items = Children.toArray(children);
  useEffect(() => { setItemsCount(items.length); }, [items.length]);
  return (
    <div className={cn('overflow-hidden', className)}>
      <motion.div
        className='flex'
        animate={{ x: `-${index * 100}%` }}
        transition={transition ?? { type: 'spring', bounce: 0.1, duration: 0.6 }}
        drag={disableDrag ? false : 'x'}
        dragConstraints={{ left: 0, right: 0 }}
      >
        {items.map((child, i) => (
          <div key={i} className='w-full shrink-0'>{child}</div>
        ))}
      </motion.div>
    </div>
  );
}

export function CarouselItem({ children, className }) {
  return <div className={cn(className)}>{children}</div>;
}

export function CarouselNavigation({ className, classNameButton, alwaysShow = false }) {
  const { index, setIndex, itemsCount } = useContext(CarouselContext);
  return (
    <div className={cn('flex items-center justify-end gap-2', className)}>
      <button type='button' aria-label='Previous' disabled={index === 0}
        onClick={() => setIndex(Math.max(0, index - 1))}
        className={cn('rounded-lg border border-seam bg-white p-2 text-stone-500 transition-colors hover:border-coal hover:text-coal disabled:opacity-40', classNameButton)}>
        <ArrowLeft className='h-4 w-4' />
      </button>
      <button type='button' aria-label='Next' disabled={index >= itemsCount - 1}
        onClick={() => setIndex(Math.min(itemsCount - 1, index + 1))}
        className={cn('rounded-lg border border-seam bg-white p-2 text-stone-500 transition-colors hover:border-coal hover:text-coal disabled:opacity-40', classNameButton)}>
        <ArrowRight className='h-4 w-4' />
      </button>
    </div>
  );
}

export function CarouselIndicator({ className, classNameButton }) {
  const { index, setIndex, itemsCount } = useContext(CarouselContext);
  return (
    <div className={cn('flex items-center justify-center gap-1.5', className)}>
      {Array.from({ length: itemsCount }).map((_, i) => (
        <button key={i} type='button' aria-label={`Go to slide ${i + 1}`} onClick={() => setIndex(i)}
          className={cn('h-1.5 rounded-full transition-all duration-300', i === index ? 'w-6 bg-coal' : 'w-1.5 bg-seamdark hover:bg-stone-400', classNameButton)} />
      ))}
    </div>
  );
}
