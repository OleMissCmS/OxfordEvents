/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./public/index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        oxford: '#13294B',
        olemiss: '#CE1126'
      }
    }
  },
  plugins: []
};

