/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'matte-black': '#171615',   // warm near-black — entire screen background
                'warm-surface': '#1e1d1c', // input bar, sidebar, card surfaces
                'warm-muted':   '#8a8988', // placeholder + secondary labels (slightly lighter than #7a7978 for WCAG AA)
                'warm-text':    '#d6d5d4', // primary body text
            },
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
