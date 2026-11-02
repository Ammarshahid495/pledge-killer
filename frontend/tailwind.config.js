/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        olive: {
          950: '#141712', // deepest charcoal olive
          900: '#1C201A', // primary dark background
          850: '#232820', // card container background
          800: '#2C3229', // card elevated surface
          750: '#343B30', // secondary container
          700: '#3F473B', // border surface
          600: '#525D4D', // subtle border / icon
          500: '#697763', // muted sage
          400: '#85967E', // sage highlight
          300: '#A4B49D', // light sage
          200: '#C8D4C3',
          100: '#E6ECE3',
        },
        cream: {
          50: '#FCF9F3',
          100: '#F7F2E7',
          200: '#F2E9D6', // Core warm almond / cream hero accent from reference image
          300: '#E7DCBE',
          400: '#D5C7A2',
          500: '#C2B185',
          600: '#9C8C61',
        },
        sage: {
          500: '#737C6E',
          600: '#5F675A',
        }
      },
      fontFamily: {
        sans: ['"Space Grotesk"', '"Plus Jakarta Sans"', 'sans-serif'],
        display: ['"Bebas Neue"', '"Barlow Condensed"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      }
    },
  },
  plugins: [],
}
