'use strict';
const video = document.querySelector('#demo-video');
const status = document.querySelector('#playback-status');
const buttons = Array.from(document.querySelectorAll('button[data-time]'));
buttons.forEach(button => button.addEventListener('click', () => {
  const seek = () => {
    video.scrollIntoView({ block: 'start', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
    video.currentTime = Math.min(Number(button.dataset.time), Math.max(0, video.duration - .1));
    video.play().catch(() => { status.textContent = 'Step selected. Press Play to continue.'; });
  };
  if (video.readyState >= 1) seek();
  else {
    status.textContent = 'Loading video metadata…';
    video.addEventListener('loadedmetadata', seek, { once: true });
    video.load();
  }
}));
video.addEventListener('timeupdate', () => {
  const current = buttons.filter(button => Number(button.dataset.time) <= video.currentTime).at(-1);
  buttons.forEach(button => {
    if (button === current) button.setAttribute('aria-current', 'true');
    else button.removeAttribute('aria-current');
  });
});
video.addEventListener('error', () => { status.textContent = 'The video could not load. Try the download link or refresh this page.'; });
