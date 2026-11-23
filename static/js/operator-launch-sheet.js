(() => {
  const printButton = document.querySelector('[data-print-launch-sheet]');
  if (!printButton) {
    return;
  }

  printButton.addEventListener('click', () => {
    window.print();
  });
})();
