/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,jsx}', './public/index.html'],
  theme: {
    extend: {
      colors: {
        control: {
          bg: '#0F172A',
          panel: '#1E293B',
          border: '#334155',
          accent: '#2563EB',
        },
      },
    },
  },
  plugins: [],
};
