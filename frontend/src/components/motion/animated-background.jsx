import { Children, cloneElement, isValidElement, useEffect, useId, useState } from 'react';
import { motion } from 'motion/react';
import { cn } from '../../lib/utils.js';

export function AnimatedBackground({ children, defaultValue, onValueChange, className, transition, enableHover = false }) {
  const [activeId, setActiveId] = useState(defaultValue ?? null);
  const uniqueId = useId();

  useEffect(() => { setActiveId(defaultValue ?? null); }, [defaultValue]);

  const handleSelect = (id) => {
    setActiveId(id);
    onValueChange?.(id);
  };

  const items = Children.toArray(children).filter(isValidElement);

  return (
    <div className={cn('relative', className)}>
      {items.map((child) => {
        const id = child.props['data-id'];
        const isActive = activeId === id;
        const extra = enableHover
          ? { onMouseEnter: () => handleSelect(id) }
          : { onClick: (e) => { child.props.onClick?.(e); handleSelect(id); } };
        return cloneElement(child, {
          key: id,
          ...extra,
          children: (
            <span className='relative z-10 inline-flex w-full items-center gap-3'>
              {isActive && (
                <motion.span
                  layoutId={`animated-background-${uniqueId}`}
                  className='absolute inset-0 -z-10 rounded-lg bg-coal/15'
                  transition={transition ?? { type: 'spring', bounce: 0.2, duration: 0.5 }}
                />
              )}
              {child.props.children}
            </span>
          ),
        });
      })}
    </div>
  );
}
