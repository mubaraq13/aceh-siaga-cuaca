import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: "#102A43",
          800: "#173F5F",
        },
        sky: {
          100: "#DCEEFF",
          50: "#F5F8FC",
        },
        status: {
          warning: "#B54708",
          danger: "#B42318",
          safe: "#18794E",
        },
      },
    },
  },
  plugins: [],
};

export default config;
