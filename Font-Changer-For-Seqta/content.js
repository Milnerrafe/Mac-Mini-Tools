const customStyle = document.createElement("style");

// Add your specific CSS rules
customStyle.textContent = `
  *, *::before, *::after {
    font-family: 'Sf Pro', sans-serif !important;
    letter-spacing: 0.03em;
  }
`;

const target = document.head || document.documentElement;
target.appendChild(customStyle);
