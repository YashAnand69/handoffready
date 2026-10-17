
"use strict";
const video = document.querySelector("video");
const status = document.querySelector("#playback-status");
document.querySelectorAll("[data-time]").forEach((button) => {
  button.addEventListener("click", () => {
    const position = Number(button.dataset.time);
    if (!Number.isFinite(position) || position < 0) return;
    video.currentTime = position;
    video.focus();
    status.textContent = `Selected ${button.textContent.trim()}. Press play to continue.`;
  });
});
video.addEventListener("error", () => {
  status.textContent = "The video could not be loaded. Read the complete transcript below or download the MP4.";
});
