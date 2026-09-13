import { InView } from '../../../components/motion/in-view.jsx';
import { TextEffect } from '../../../components/motion/text-effect.jsx';
import { Accordion, AccordionAnimatedItem } from '../../../components/motion/accordion.jsx';

const FAQS = [
  [
    'Does any data leave my machine?',
    'No. Parsing, OCR, embeddings and language models all run locally. After the one-time model download the network cable can stay unplugged — the app never calls an external service, and there is no telemetry.',
  ],
  [
    'What kinds of files does it take?',
    'Digital and scanned PDFs, Word documents, Excel workbooks, CSVs and images. Scanned pages go through OCR; ruled tables are detected as table regions; multi-sheet workbooks are read sheet by sheet.',
  ],
  [
    'What exactly is a "receipt"?',
    'The path from an answer back to its source: document, page, table and cell or row. Every fact, chat citation, chart bar and report table links through the index to the stored original — you read the figure where it was printed, not where the system remembered it.',
  ],
  [
    'What happens when two documents disagree?',
    'Nothing is silently picked. Values that disagree on the same entity, metric and period are shown side by side in chat, reports and the Conflict Radar, with likely causes and a status the officer sets: open, acknowledged or resolved.',
  ],
  [
    'Does it need an LLM to be useful?',
    'No. Without a model it runs in extractive mode — verbatim evidence snippets with citations, no generation. With Ollama or local Transformers available, answers, summaries and the analytical agent come online. The fact index and search never depend on a generative model.',
  ],
  [
    'How do I start without my own files?',
    'One click generates a demonstration corpus — a digital annual report, a scanned geological report, a mixed PDF, a multi-sheet workbook and a parliamentary DOCX — ingests it, and immediately shows conflicts, receipts and reports working end to end.',
  ],
];

export function Faq() {
  return (
    <section id='faq' className='py-24 md:py-28'>
      <div className='mx-auto max-w-6xl px-5 md:px-8'>

        {/* Heading row */}
        <InView className='max-w-2xl'>
          <TextEffect
            as='h2'
            per='word'
            preset='fade-in-blur'
            className='text-2xl font-bold tracking-[-0.02em] md:text-3xl'
          >
            Before you open the workspace.
          </TextEffect>
        </InView>

        {/* Description sits directly above the accordion cards */}
        <InView
          variants={{ hidden: { opacity: 0, y: 10 }, visible: { opacity: 1, y: 0 } }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className='mt-3 mb-8 max-w-[58ch] text-[14px] leading-relaxed text-stone-500'
        >
          Everything else is in the architecture notes — or just load the
          demonstration corpus and poke at it.
        </InView>

        {/* Accordion cards */}
        <InView
          variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
          transition={{ duration: 0.6, delay: 0.15 }}
        >
          <Accordion>
            {FAQS.map(([q, a], i) => (
              <AccordionAnimatedItem key={q} value={`faq-${i}`} title={q}>
                {a}
              </AccordionAnimatedItem>
            ))}
          </Accordion>
        </InView>

      </div>
    </section>
  );
}
