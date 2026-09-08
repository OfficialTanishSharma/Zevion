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
        chatgpt: {
          bg: '#212121',
          sidebar: '#171717',
          card: '#2f2f2f',
          hover: '#383838',
          border: '#424242',
          accent: '#10a37f',
          accentHover: '#1a7f64',
          userBubble: '#303030',
          aiBubble: '#212121',
          text: '#ececec',
          subtext: '#b4b4b4'
        },
        win11: {
          taskbar: 'rgba(28, 33, 40, 0.85)',
          window: '#202020',
          header: '#2c2c2c',
          accent: '#0078d4'
        }
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ripple': 'ripple 1s cubic-bezier(0, 0.2, 0.8, 1) infinite',
        'flash': 'flash 0.5s ease-out',
        'typing': 'blink 1s step-end infinite'
      },
      keyframes: {
        ripple: {
          '0%': { transform: 'scale(0.8)', opacity: '1' },
          '100%': { transform: 'scale(2.4)', opacity: '0' }
        },
        flash: {
          '0%': { opacity: '0.9', background: 'white' },
          '100%': { opacity: '0', background: 'transparent' }
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' }
        }
      }
    },
  },
  plugins: [],
}
