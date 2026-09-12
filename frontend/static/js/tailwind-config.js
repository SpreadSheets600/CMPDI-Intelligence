// Tailwind Play CDN configuration: the single source of the design system.
// Every palette step is a CSS variable that flips under .dark (see
// base.html), so the whole content area re-themes from one place. The
// sidebar keeps its own fixed charcoal palette (--s-*) in both themes.
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Archivo', 'ui-sans-serif', 'sans-serif'],
        mono: ['IBM Plex Mono', 'ui-monospace', 'monospace'],
      },
      colors: {
        paper: 'rgb(var(--c-paper) / <alpha-value>)',
        white: 'rgb(var(--c-surface) / <alpha-value>)',
        ink: 'rgb(var(--c-ink) / <alpha-value>)',
        seam: 'rgb(var(--c-seam) / <alpha-value>)',
        seamdark: 'rgb(var(--c-seamdark) / <alpha-value>)',
        coal: 'rgb(var(--c-coal) / <alpha-value>)',
        coalsoft: 'rgb(var(--c-coalsoft) / <alpha-value>)',
        coalline: 'rgb(var(--c-coalline) / <alpha-value>)',
        side: 'rgb(var(--s-bg) / <alpha-value>)',
        sidecard: 'rgb(var(--s-hi) / <alpha-value>)',
        sidetext: 'rgb(var(--s-text) / <alpha-value>)',
        sidemute: 'rgb(var(--s-mute) / <alpha-value>)',
        sideline: 'rgb(var(--s-line) / <alpha-value>)',
        stone: {
          300: 'rgb(var(--c-muted0) / <alpha-value>)',
          400: 'rgb(var(--c-muted1) / <alpha-value>)',
          500: 'rgb(var(--c-muted2) / <alpha-value>)',
          600: 'rgb(var(--c-muted3) / <alpha-value>)',
          700: 'rgb(var(--c-muted4) / <alpha-value>)',
        },
        emerald: {
          50: 'rgb(var(--c-ok-bg) / <alpha-value>)',
          200: 'rgb(var(--c-ok-line) / <alpha-value>)',
          600: 'rgb(var(--c-ok-solid) / <alpha-value>)',
          700: 'rgb(var(--c-ok-text) / <alpha-value>)',
          800: 'rgb(var(--c-ok-text2) / <alpha-value>)',
        },
        red: {
          50: 'rgb(var(--c-bad-bg) / <alpha-value>)',
          200: 'rgb(var(--c-bad-line) / <alpha-value>)',
          300: 'rgb(var(--c-bad-line2) / <alpha-value>)',
          600: 'rgb(var(--c-bad-solid) / <alpha-value>)',
          700: 'rgb(var(--c-bad-text) / <alpha-value>)',
        },
        amber: {
          100: 'rgb(var(--c-warn-bg) / <alpha-value>)',
          900: 'rgb(var(--c-warn-text) / <alpha-value>)',
        },
      },
      boxShadow: {
        card: '0 1px 2px rgb(28 25 23 / 0.05)',
        lift: '0 10px 24px -8px rgb(28 25 23 / 0.18)',
      },
      keyframes: {
        rise: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fade: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        pop: {
          '0%': { opacity: '0', transform: 'scale(.96)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        // landing page: format marquee, floating annotation cards and the
        // breathing glow on the final call-to-action (all pure CSS loops;
        // entrance/scroll animations are driven by Motion in landing.js)
        marquee: {
          to: { transform: 'translateX(-50%)' },
        },
        'float-y': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-9px)' },
        },
        'cta-breathe': {
          '0%, 100%': { boxShadow: '0 4px 18px rgb(var(--c-coal) / 0.35)' },
          '50%': { boxShadow: '0 6px 32px rgb(var(--c-coal) / 0.6)' },
        },
      },
      animation: {
        rise: 'rise .5s cubic-bezier(.16,1,.3,1) both',
        fade: 'fade .4s ease both',
        pop: 'pop .3s cubic-bezier(.16,1,.3,1) both',
        marquee: 'marquee 36s linear infinite',
        'float-y': 'float-y 7s ease-in-out infinite',
        'float-y-slow': 'float-y 9s ease-in-out 1.2s infinite',
        'cta-breathe': 'cta-breathe 3.4s ease-in-out 1.8s infinite',
      },
    },
  },
}
