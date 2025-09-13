// tailwind.config.js

/** @type {import('tailwindcss').Config} */
module.exports = {
    // ... your existing config
    plugins: [
        require("tailwindcss-animate"),
        require("@tailwindcss/typography"), // <-- ADD THIS LINE
    ],
}