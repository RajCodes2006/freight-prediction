(() => {
  const MODEL_CLASSES = ["HSI", "SI", "PI", "CI"];
  let scheduled = false;

  const getModelClass = () => {
    const tag = document.querySelector(".chart-tag");
    const tagMatch = tag?.textContent?.match(/\b(HSI|SI|PI|CI)\b/);
    if (tagMatch) return tagMatch[1];

    const heading = Array.from(document.querySelectorAll("h3")).find((el) =>
      /Index Outlook$/i.test(el.textContent.trim())
    );
    const headingMatch = heading?.textContent?.match(/\b(HSI|SI|PI|CI)\b/i);
    return headingMatch ? headingMatch[1].toUpperCase() : null;
  };

  const injectAboutButtonStyles = () => {
    if (document.getElementById("about-button-styles")) return;

    const style = document.createElement("style");
    style.id = "about-button-styles";
    style.textContent = `
      .about-button {
        height: 34px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 7px;
        padding: 0 11px;
        border: 1px solid #2a3942;
        border-radius: 999px;
        background: #111c23;
        color: #dce5e9;
        font-family: "DM Mono", monospace;
        font-size: 8px;
        font-weight: 500;
        letter-spacing: .05em;
        text-decoration: none;
        transition: border-color .18s ease, color .18s ease, background .18s ease, transform .18s ease;
      }
      .about-button:hover {
        border-color: #dbe92f;
        color: #dbe92f;
        transform: translateY(-1px);
      }
      .about-button svg { flex: none; }
      html[data-theme="light"] .about-button {
        border-color: #dfe4e7;
        background: #fff;
        color: #63717a;
      }
      html[data-theme="light"] .about-button:hover {
        border-color: #b4bd59;
        color: #66701e;
      }
      @media (max-width: 620px) {
        .about-button {
          width: 34px;
          padding: 0;
        }
        .about-button span:last-child { display: none; }
      }
    `;
    document.head.appendChild(style);
  };

  const injectAboutButton = () => {
    const actions = document.querySelector(".topbar-actions");
    if (!actions || actions.querySelector(".about-button")) return;

    injectAboutButtonStyles();

    const link = document.createElement("a");
    link.href = "/about.html";
    link.className = "about-button";
    link.setAttribute("aria-label", "Open About page");
    link.setAttribute("title", "About Freight Prediction");
    link.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.8" />
        <path d="M12 10v6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
        <circle cx="12" cy="7" r="1" fill="currentColor" />
      </svg>
      <span>ABOUT</span>
    `;

    const themeToggle = actions.querySelector(".theme-toggle");
    if (themeToggle) {
      actions.insertBefore(link, themeToggle);
    } else {
      actions.prepend(link);
    }
  };

  const refresh = () => {
    if (scheduled) return;
    scheduled = true;

    requestAnimationFrame(() => {
      scheduled = false;
      injectAboutButton();

      const modelClass = getModelClass();
      if (!modelClass || !MODEL_CLASSES.includes(modelClass)) return;

      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT
      );
      const nodes = [];
      let node;

      while ((node = walker.nextNode())) {
        const value = node.nodeValue?.trim();
        if (value === "Current PI Index" || value === "PI Index") {
          nodes.push(node);
        }
      }

      nodes.forEach((textNode) => {
        textNode.nodeValue = textNode.nodeValue.replace("PI", modelClass);
      });
    });
  };

  document.title = "Freight Predictor";
  injectAboutButtonStyles();

  new MutationObserver(refresh).observe(document.documentElement, {
    subtree: true,
    childList: true,
    characterData: true,
  });

  refresh();
})();
