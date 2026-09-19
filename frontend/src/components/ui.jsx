import { Link } from 'react-router-dom';
import { TextEffect } from './motion/text-effect.jsx';
import { AnimatedGroup } from './motion/animated-group.jsx';
import { InView } from './motion/in-view.jsx';
import { TextShimmer } from './motion/text-shimmer.jsx';
import { GlowEffect } from './motion/glow-effect.jsx';

// ─── Consolidated UI Primitives ─────────────────────────────────────────────

export function Card({
  children,
  className = '',
  interactive = false,
  highlight = false,
  as: Component = 'div',
  ...props
}) {
  return (
    <Component
      className={`rounded-xl border bg-white shadow-card transition-all duration-150 ${
        highlight
          ? 'border-coalline bg-coalsoft/30'
          : 'border-seam'
      } ${
        interactive
          ? 'cursor-pointer hover:border-coal/60 hover:shadow-lift'
          : ''
      } ${className}`}
      {...props}
    >
      {children}
    </Component>
  );
}

export function SectionTitle({
  title,
  subtitle,
  badge,
  action,
  className = '',
  id,
}) {
  return (
    <div id={id} className={`mb-3 flex flex-wrap items-center justify-between gap-2 ${className}`}>
      <div className='flex items-center gap-2'>
        <h2 className='text-[13px] font-semibold uppercase tracking-wider text-stone-400'>
          {title}
        </h2>
        {badge}
      </div>
      {(subtitle || action) && (
        <div className='flex items-center gap-3'>
          {subtitle && <span className='text-[12px] text-stone-400'>{subtitle}</span>}
          {action}
        </div>
      )}
    </div>
  );
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  icon: Icon,
  iconRight: IconRight,
  disabled = false,
  to,
  href,
  className = '',
  type = 'button',
  ...props
}) {
  const baseCls =
    'inline-flex items-center justify-center font-medium transition-all duration-150 select-none disabled:opacity-50 disabled:pointer-events-none active:scale-[0.99]';

  const sizeCls = {
    sm: 'px-2.5 py-1 text-[12px] rounded-lg gap-1.5',
    md: 'px-3.5 py-2 text-[13px] rounded-lg gap-2',
    lg: 'px-5 py-2.5 text-sm rounded-lg gap-2',
  }[size] || 'px-3.5 py-2 text-[13px] rounded-lg gap-2';

  const variantCls = {
    primary:
      'bg-coal text-white font-semibold shadow-card hover:bg-amber-500 hover:shadow-lift',
    secondary:
      'border border-seam bg-white text-ink shadow-card hover:border-coal hover:text-coal',
    ghost:
      'border border-seam bg-transparent text-stone-600 hover:border-coal hover:text-coal hover:bg-coalsoft/30',
    danger:
      'bg-red-600 text-white font-semibold hover:bg-red-700 shadow-card',
    'danger-ghost':
      'border border-red-200 bg-red-50 text-red-700 hover:bg-red-100',
  }[variant] || 'bg-coal text-white font-semibold hover:bg-amber-500';

  const fullCls = `${baseCls} ${sizeCls} ${variantCls} ${className}`;

  if (to) {
    return (
      <Link to={to} className={fullCls} {...props}>
        {Icon && <Icon className='h-4 w-4 shrink-0' />}
        {children}
        {IconRight && <IconRight className='h-4 w-4 shrink-0' />}
      </Link>
    );
  }

  if (href) {
    return (
      <a href={href} className={fullCls} {...props}>
        {Icon && <Icon className='h-4 w-4 shrink-0' />}
        {children}
        {IconRight && <IconRight className='h-4 w-4 shrink-0' />}
      </a>
    );
  }

  return (
    <button type={type} disabled={disabled} className={fullCls} {...props}>
      {Icon && <Icon className='h-4 w-4 shrink-0' />}
      {children}
      {IconRight && <IconRight className='h-4 w-4 shrink-0' />}
    </button>
  );
}

export function Badge({
  children,
  variant = 'neutral',
  size = 'sm',
  icon: Icon,
  className = '',
  ...props
}) {
  const variantCls = {
    neutral: 'border-seam bg-paper text-stone-600',
    coal: 'border-coalline bg-coalsoft text-coal',
    ok: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    bad: 'border-red-200 bg-red-50 text-red-700',
    warn: 'border-amber-200 bg-amber-100 text-amber-900',
  }[variant] || 'border-seam bg-paper text-stone-600';

  const sizeCls = size === 'md'
    ? 'px-3 py-1 text-[11.5px]'
    : 'px-2.5 py-0.5 text-[10.5px]';

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-mono uppercase tracking-wide font-medium ${sizeCls} ${variantCls} ${className}`}
      {...props}
    >
      {Icon && <Icon className='h-3 w-3 shrink-0' />}
      {children}
    </span>
  );
}

export const Chip = Badge;

export function Table({ children, className = '', containerClassName = '' }) {
  return (
    <div className={`overflow-x-auto rounded-xl border border-seam bg-white shadow-card ${containerClassName}`}>
      <table className={`w-full text-left text-[13px] ${className}`}>
        {children}
      </table>
    </div>
  );
}

export function TableHead({ children, className = '' }) {
  return (
    <thead className={`border-b border-seam bg-paper text-left font-mono text-[11px] uppercase tracking-wider text-stone-500 ${className}`}>
      {children}
    </thead>
  );
}

export function TableBody({ children, className = '' }) {
  return <tbody className={`divide-y divide-seam ${className}`}>{children}</tbody>;
}

export function TableRow({ children, className = '', ...props }) {
  return (
    <tr
      className={`border-b border-seam last:border-0 hover:bg-paper/40 transition-colors ${className}`}
      {...props}
    >
      {children}
    </tr>
  );
}

export function TableHeader({ children, className = '', numeric = false, ...props }) {
  return (
    <th
      className={`px-4 py-2.5 font-medium whitespace-nowrap ${
        numeric ? 'text-right' : 'text-left'
      } ${className}`}
      {...props}
    >
      {children}
    </th>
  );
}

export function TableCell({ children, className = '', numeric = false, mono = false, ...props }) {
  return (
    <td
      className={`px-4 py-2 text-ink whitespace-nowrap ${
        numeric ? 'text-right font-mono tabular-nums' : mono ? 'font-mono' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </td>
  );
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className = '',
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-xl border border-dashed border-seamdark bg-white px-6 py-12 text-center shadow-card ${className}`}
    >
      {Icon && (
        <span className='flex h-12 w-12 items-center justify-center rounded-xl bg-coalsoft text-coal mb-3'>
          <Icon className='h-6 w-6' />
        </span>
      )}
      {title && <h3 className='text-[15px] font-semibold text-ink'>{title}</h3>}
      {description && (
        <p className='mt-1 max-w-[45ch] text-[13px] text-stone-500 leading-relaxed'>
          {description}
        </p>
      )}
      {action && <div className='mt-4'>{action}</div>}
    </div>
  );
}

export function Skeleton({ className = '' }) {
  return (
    <div className={`animate-pulse rounded-lg bg-stone-200/70 dark:bg-stone-700/40 ${className}`} />
  );
}

// ─── Workspace Structure Primitives ─────────────────────────────────────────

// Page header used by every workspace screen.
// Title animates per-word with the TextEffect preset; subtitle fades in.
export function PageHeader({ title, subtitle, children }) {
  return (
    <div className='flex flex-wrap items-start justify-between gap-3'>
      <div className='min-w-0'>
        <TextEffect as='h1' per='word' preset='fade-in-blur' trigger={true}
          className='text-2xl font-semibold tracking-tight'>
          {title}
        </TextEffect>
        {subtitle && (
          <TextEffect as='p' per='line' preset='fade' delay={0.15}
            className='mt-1 max-w-[70ch] text-[15px] text-stone-500'>
            {subtitle}
          </TextEffect>
        )}
      </div>
      {children}
    </div>
  );
}

// Standard staggered entrance for page content (above the fold).
export function Rise({ delay = 0, className = '', children }) {
  return (
    <AnimatedGroup preset='blur-slide' className={className}>
      <div style={{ animationDelay: `${delay}s` }}>{children}</div>
    </AnimatedGroup>
  );
}

// Scroll-triggered entrance for below-the-fold sections.
export function Reveal({ className = '', children }) {
  return (
    <InView
      className={className}
      variants={{ hidden: { opacity: 0, y: 16 }, visible: { opacity: 1, y: 0 } }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </InView>
  );
}

export function Loading({ label = 'Loading workspace data…' }) {
  return (
    <div className='relative mx-auto mt-16 max-w-md overflow-hidden rounded-2xl border border-seam bg-white p-8 text-center shadow-card'>

      {/* Branded Pulse Icon */}
      <div className='relative mx-auto flex h-14 w-14 items-center justify-center'>
        <span className='absolute inset-0 animate-ping rounded-2xl bg-coal/20 duration-1000' />
        <span className='relative flex h-12 w-12 items-center justify-center rounded-xl bg-coal font-mono text-base font-bold text-white shadow-[0_4px_14px_rgba(234,138,12,0.4)]'>
          C
        </span>
      </div>

      {/* Shimmering label */}
      <div className='mt-5'>
        <TextShimmer as='p' duration={2} className='text-[14px] font-semibold text-ink'>
          {label}
        </TextShimmer>
        <p className='mt-1 font-mono text-[11px] text-stone-400'>
          Offline document intelligence · local verification
        </p>
      </div>

      {/* Subtle Skeleton progress bars */}
      <div className='mx-auto mt-5 max-w-[200px] space-y-2'>
        <div className='h-1.5 w-full overflow-hidden rounded-full bg-paper'>
          <div className='h-full w-2/3 animate-[pulse_1.5s_ease-in-out_infinite] rounded-full bg-coal/50' />
        </div>
        <div className='h-1 w-3/4 mx-auto overflow-hidden rounded-full bg-paper'>
          <div className='h-full w-1/2 animate-[pulse_1.2s_ease-in-out_infinite] rounded-full bg-coal/30' />
        </div>
      </div>
    </div>
  );
}

export function ErrorBox({ message, onRetry }) {
  return (
    <div className='relative mt-6 overflow-hidden rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13.5px] text-red-700'>
      <GlowEffect colors={['#fecaca', '#fca5a5', '#fecaca']} mode='static' blur='soft' className='opacity-60' />
      <div className='relative flex items-center justify-between gap-3'>
        <span>{message}</span>
        {onRetry && (
          <button
            type='button'
            onClick={onRetry}
            className='rounded-md border border-red-300 bg-white/80 px-2.5 py-1 text-[11px] font-semibold text-red-700 hover:bg-white'
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
