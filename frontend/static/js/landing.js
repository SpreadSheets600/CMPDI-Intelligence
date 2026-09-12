// Landing page entry. ES modules are deferred by default, so the DOM is
// ready when these run. Each behaviour lives in its own file under
// static/js/landing/.
import { initTheme } from "./landing/theme.js";
import { initNav } from "./landing/nav.js";
import { initReveals } from "./landing/reveal.js";
import { initCountUp } from "./landing/countup.js";
import { initFaq } from "./landing/faq.js";

initTheme();
initNav();
initReveals();
initCountUp();
initFaq();
