document.addEventListener("click", (event) => {
  const copyButton = event.target.closest("[data-copy-link]");
  if (copyButton) {
    navigator.clipboard.writeText(window.location.href).then(() => {
      const previous = copyButton.textContent;
      copyButton.textContent = "Enlace copiado ✓";
      window.setTimeout(() => { copyButton.textContent = previous; }, 1800);
    });
    return;
  }

  const button = event.target.closest("[data-play]");
  if (!button) return;

  const shell = button.closest("[data-player]");
  const videoId = shell?.dataset.videoId;
  if (!shell || !videoId) return;

  const iframe = document.createElement("iframe");
  iframe.src = `https://www.youtube-nocookie.com/embed/${encodeURIComponent(videoId)}?autoplay=1&rel=0`;
  iframe.title = button.getAttribute("aria-label") || "Reproductor de YouTube";
  iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
  iframe.allowFullscreen = true;
  iframe.referrerPolicy = "strict-origin-when-cross-origin";
  shell.replaceChildren(iframe);
  shell.classList.add("is-playing");
});

document.querySelectorAll("form.filters").forEach((form) => {
  form.addEventListener("submit", () => {
    form.querySelectorAll("input, select").forEach((control) => {
      if (!control.value) control.disabled = true;
    });
  });
});
