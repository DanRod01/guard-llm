export default {
  darkMode: 'class',
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './composables/**/*.{js,ts}',
    './app.vue',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        surface: {
          950: '#09090b', // Deepest background (Linear / Vercel style)
          900: '#111114', // Card background
          850: '#18181b', // Elevated surface
          800: '#27272a', // Borders / dividers
          750: '#323238', // Hover borders
          700: '#3f3f46', // Secondary text / icons
        },
        accent: {
          DEFAULT: '#10b981',
          hover: '#059669',
          muted: 'rgba(16, 185, 129, 0.1)',
        },
      },
    },
  },
}
