import { Compass, LayoutDashboard, Search, MessageCircle } from 'lucide-react';
import { Rise, PageHeader, Card, Button } from '../components/ui.jsx';

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
        <Card className='mx-auto mt-10 flex max-w-md flex-col items-center p-8 text-center'>
          <span className='flex h-12 w-12 items-center justify-center rounded-xl bg-coalsoft text-coal'>
            <Compass className='h-6 w-6' />
          </span>
          <p className='mt-4 font-mono text-xs text-muted1'>{window.location.pathname}</p>
          <div className='mt-6 flex flex-wrap justify-center gap-2.5'>
            {LINKS.map(({ to, label, Icon }) => (
              <Button
                key={to}
                to={to}
                variant='secondary'
                size='sm'
              >
                <Icon className='h-3.5 w-3.5 text-muted1' /> {label}
              </Button>
            ))}
          </div>
        </Card>
      </Rise>
    </div>
  );
}
