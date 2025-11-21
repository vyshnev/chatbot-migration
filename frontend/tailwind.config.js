/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'matte-black': '#46484d',
            },
        },
    },
    plugins: [
        require('@tailwindcss/typography'),
    ],
}
