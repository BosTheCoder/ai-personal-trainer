/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
        'glass-inset': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
      },
      backgroundColor: {
        'glass': 'rgba(255, 255, 255, 0.25)',
        'glass-dark': 'rgba(255, 255, 255, 0.1)',
      },
      borderColor: {
        'glass': 'rgba(255, 255, 255, 0.18)',
      },
    },
  },
  plugins: [],
}
