import { ScrollProgress } from '../../components/motion/scroll-progress.jsx';
import { Nav } from './sections/Nav.jsx';
import { Hero } from './sections/Hero.jsx';
import { Stats } from './sections/Stats.jsx';
import { Product } from './sections/Product.jsx';
import { Pipeline } from './sections/Pipeline.jsx';
import { Capabilities } from './sections/Capabilities.jsx';
import { Testimonials } from './sections/Testimonials.jsx';
import { Faq } from './sections/Faq.jsx';
import { Cta } from './sections/Cta.jsx';
import { Footer } from './sections/Footer.jsx';
import { usePageData } from '../../hooks/useData.js';

export default function Landing() {
  const { data } = usePageData('/api/pages/landing');
  const stats = data?.stats;

  return (
    <div className='min-h-dvh bg-paper text-ink'>
      <ScrollProgress className='z-[60] h-[2px] bg-coal' />
      <Nav />
      <main>
        <Hero stats={stats} />
        <Stats stats={stats} />
        <Product />
        <Pipeline />
        <Capabilities />
        <Testimonials />
        <Faq />
        <Cta />
      </main>
      <Footer />
    </div>
  );
}
