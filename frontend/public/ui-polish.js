(() => {
  const MODEL_CLASSES = ["HSI", "SI", "PI", "CI"];
  const navMap = {
    overview: "#overview",
    forecast: "#forecast",
    vessels: "#vessels",
    ports: "#ports",
    contract: "#contract",
  };

  let focusTimer = null;
  let scrollRaf = null;

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

  const injectStyles = () => {
    if (document.getElementById("freight-nav-polish")) return;

    const style = document.createElement("style");
    style.id = "freight-nav-polish";
    style.textContent = `
      html { scroll-behavior: smooth; }

      #overview, #forecast, #vessels, #ports, #contract {
        scroll-margin-top: 24px;
        transition: transform 220ms ease, box-shadow 220ms ease, border-color 220ms ease;
        will-change: transform;
      }

      /* React keeps a legacy .active on Overview. Neutralize it unless that
         same link is the JS-selected navigation target, so two items can never
         look selected at once. */
      .sidebar nav a.active:not(.freight-nav-active) {
        color: #96a3ad !important;
        background: transparent !important;
        box-shadow: none !important;
      }

      .sidebar nav a.freight-nav-active {
        color: #f3f7f9 !important;
        background: #1a252d !important;
        box-shadow: inset 3px 0 0 #e4ef37, 0 6px 18px rgba(16, 23, 29, 0.08);
      }

      #overview.freight-nav-focus,
      #forecast.freight-nav-focus,
      #vessels.freight-nav-focus,
      #ports.freight-nav-focus,
      #contract.freight-nav-focus {
        transform: translateY(-5px);
        box-shadow: 0 14px 34px rgba(16, 24, 30, 0.12), 0 0 0 1px rgba(228, 239, 55, 0.28);
      }

      .freight-nav-focus::before {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        border-radius: inherit;
        box-shadow: inset 0 0 0 1px rgba(228, 239, 55, 0.14);
      }
    `;
    document.head.appendChild(style);
  };

  const getLinks = () => Array.from(document.querySelectorAll(".sidebar nav a[href]"));

  const setActive = (id) => {
    getLinks().forEach((link) => {
      const active = link.getAttribute("href") === `#${id}`;

      link.classList.remove("active");
      link.classList.toggle("freight-nav-active", active);

      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  };

  const focusSection = (id) => {
    const target = document.getElementById(id);
    if (!target) return;

    if (focusTimer) window.clearTimeout(focusTimer);
    target.classList.remove("freight-nav-focus");

    requestAnimationFrame(() => {
      target.classList.add("freight-nav-focus");
      focusTimer = window.setTimeout(() => {
        target.classList.remove("freight-nav-focus");
      }, 900);
    });
  };

  const getSections = () =>
    Object.entries(navMap)
      .map(([id, selector]) => ({
        id,
        element: document.querySelector(selector),
      }))
      .filter(({ element }) => element);

  const updateActiveFromScroll = () => {
    const sections = getSections().sort(
      (a, b) => a.element.getBoundingClientRect().top - b.element.getBoundingClientRect().top
    );
    if (!sections.length) return;

    const guideLine = Math.max(100, window.innerHeight * 0.30);
    let active = sections[0];

    for (const section of sections) {
      if (section.element.getBoundingClientRect().top <= guideLine) active = section;
    }

    setActive(active.id);
  };

  const scheduleScrollUpdate = () => {
    if (scrollRaf) return;

    scrollRaf = requestAnimationFrame(() => {
      scrollRaf = null;
      updateActiveFromScroll();
    });
  };

  const setupNavigation = () => {
    injectStyles();

    const navLinks = getLinks();
    if (!navLinks.length) return;

    navLinks.forEach((link) => {
      if (link.dataset.freightNavReady === "true") return;
      link.dataset.freightNavReady = "true";

      link.addEventListener("click", (event) => {
        const href = link.getAttribute("href");
        if (!href || !href.startsWith("#")) return;

        const target = document.querySelector(href);
        if (!target) return;

        event.preventDefault();
        const id = href.slice(1);

        setActive(id);
        focusSection(id);
        target.scrollIntoView({ behavior: "smooth", block: "start" });

        if (window.history?.replaceState) {
          window.history.replaceState(null, "", href);
        }

        link.blur();
      });
    });

    const hash = window.location.hash.slice(1);
    if (hash && navMap[hash]) setActive(hash);
    else updateActiveFromScroll();
  };

  const refreshLabels = () => {
    const modelClass = getModelClass();
    if (!modelClass || !MODEL_CLASSES.includes(modelClass)) return;

    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const nodes = [];
    let node;

    while ((node = walker.nextNode())) {
      const value = node.nodeValue?.trim();
      if (value === "Current PI Index" || value === "PI Index") nodes.push(node);
    }

    nodes.forEach((textNode) => {
      textNode.nodeValue = textNode.nodeValue.replace("PI", modelClass);
    });
  };

  document.title = "Freight Predictor";
  injectStyles();
  setupNavigation();
  refreshLabels();

  window.addEventListener("scroll", scheduleScrollUpdate, { passive: true });
  window.addEventListener("resize", scheduleScrollUpdate, { passive: true });

  const observer = new MutationObserver(() => {
    setupNavigation();
    refreshLabels();
  });

  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    characterData: true,
  });
})();
