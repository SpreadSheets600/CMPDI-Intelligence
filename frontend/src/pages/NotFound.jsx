import { Link } from 'react-router-dom';
import { Compass, LayoutDashboard, Search, MessageCircle } from 'lucide-react';
import { Rise, PageHeader } from '../components/ui.jsx';

const LINKS = [
  { to: '/dashboard', label: 'Dashboard', Icon: LayoutDashboard },
  { to: '/search', label: 'Search', Icon: Search },
  { to: '/ask', label: 'Ask', Icon: MessageCircle },
];

export default function NotFound() {
  return (
    <div>
      <PageHeader
        title='Page not found'
        subtitle='The address does not match any screen. The library itself is untouched.'
      />
      <Rise delay={0.05}>
        <div className='mx-auto mt-10 flex max-w-md flex-col items-center rounded-xl border border-seam bg-white p-8 text-center shadow-card'>
          <span className='flex h-12 w-12 items-center justify-center rounded-xl bg-coalsoft text-coal'>
            <Compass className='h-6 w-6' />
          </span>
          <p className='mt-4 font-mono text-[12px] text-stone-400'>{window.location.pathname}</p>
          <div className='mt-5 flex flex-wrap justify-center gap-2'>
            {LINKS.map(({ to, label, Icon }) => (
              <Link
                key={to}
                to={to}
                className='flex items-center gap-1.5 rounded-lg border border-seam px-3.5 py-2 text-[13px] font-medium text-stone-600 transition-colors hover:border-coal hover:text-coal'
              >
                <Icon className='h-3.5 w-3.5' /> {label}
              </Link>
            ))}
          </div>
        </div>
      </Rise>
    </div>
  );
}
