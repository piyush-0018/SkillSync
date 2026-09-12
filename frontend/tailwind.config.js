/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        soft: '0 12px 32px -18px rgba(15, 23, 42, 0.24)',
      },
      colors: {
        blue: {
          50: '#f0f3ff',
          100: '#e1e7ff',
          200: '#c2ceff',
          300: '#99aaff',
          400: '#6b7cff',
          500: '#3f51dc',
          600: '#1428a0',
          700: '#101f80',
          800: '#0d1966',
          900: '#0b1554',
          950: '#050a2b',
        },
        indigo: {
          50: '#f0f3ff',
          100: '#e1e7ff',
          200: '#c2ceff',
          300: '#99aaff',
          400: '#6b7cff',
          500: '#3f51dc',
          600: '#1428a0',
          700: '#101f80',
          800: '#0d1966',
          900: '#0b1554',
          950: '#050a2b',
        },
      },
    },
  },
  plugins: [],
}
