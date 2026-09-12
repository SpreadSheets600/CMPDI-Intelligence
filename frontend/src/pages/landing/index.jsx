import { motion } from "framer-motion";
import { Nav, Hero, SocialProof } from "./sections/Hero.jsx";
import { Showcase, Pipeline, Capabilities, FieldNotes } from "./sections/Showcase.jsx";
import { Faq, FinalCta, Footer } from "./sections/Closing.jsx";
import { usePageData } from "../../hooks/useData.js";

export default function Landing() {
  // live database counts for the social-proof band (like the Jinja page)
  const { data } = usePageData("/api/pages/landing");
  const stats = data?.stats;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="min-h-dvh bg-paper text-ink">
      <Nav />
      <main>
        <Hero stats={stats} />
        <SocialProof stats={stats} />
        <Showcase />
        <Pipeline />
        <Capabilities />
        <FieldNotes />
        <Faq />
        <FinalCta />
      </main>
      <Footer />
    </motion.div>
  );
}
