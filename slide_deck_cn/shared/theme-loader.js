(function () {
  const THEMES = {
    paper: 'theme-paper.css',
    mist: 'theme-mist.css',
    sage: 'theme-sage.css',
  };

  const params = new URLSearchParams(window.location.search);
  const requested = params.get('theme') || 'paper';
  const theme = THEMES[requested] ? requested : 'paper';

  document.documentElement.dataset.theme = theme;

  window.addEventListener('DOMContentLoaded', () => {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '../shared/' + THEMES[theme];
    document.head.appendChild(link);
  });
})();
