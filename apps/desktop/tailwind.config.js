/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0B1020',
        surface: '#111827',
        secondary: '#1F2937',
        accent: {
          DEFAULT: '#6366F1',
          hover: '#4F46E5',
          glow: 'rgba(99, 102, 241, 0.25)',
        },
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        text: '#F9FAFB',
        muted: '#9CA3AF',
      },
      fontFamily: {
        sans: ['Poppins', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 20px -3px rgba(99, 102, 241, 0.25)',
        'glow-danger': '0 0 20px -3px rgba(239, 68, 68, 0.25)',
        'glow-success': '0 0 20px -3px rgba(16, 185, 129, 0.25)',
      },
    },
  },
  plugins: [],
};
