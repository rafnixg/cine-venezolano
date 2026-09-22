document.addEventListener("click", (event) => {
  const aiButton = event.target.closest("[data-ai-apply]");
  if (aiButton) {
    const container = aiButton.closest("[data-ai-suggestion]");
    const form = document.querySelector("[data-editor-form]");
    try {
      const suggestion = JSON.parse(container.dataset.suggestion);
      ["title", "original_title", "synopsis", "year", "country", "language", "subtitles", "content_type", "length_category"].forEach((name) => {
        const field = form?.elements.namedItem(name);
        if (field) field.value = suggestion[name] ?? "";
      });
      ["genres", "tags", "directors", "cast"].forEach((name) => {
        const field = form?.elements.namedItem(name);
        if (field) field.value = (suggestion[name] || []).join(", ");
      });
      aiButton.textContent = "Propuesta cargada ✓";
      container.querySelector("[data-ai-note]").textContent = "Ahora revisa los campos antes de guardar.";
    } catch (_error) { aiButton.textContent = "No se pudo cargar la propuesta"; }
    return;
  }

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
