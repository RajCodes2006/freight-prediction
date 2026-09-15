(() => {
  const MODEL_CLASSES = ["HSI", "SI", "PI", "CI"];
  let refreshScheduled = false;
  let navigationScheduled = false;
  let observer;
  let scrollHandler;

  const navMap = {
    overview: "#overview",
    forecast: "#forecast",
    vessels: "#vessels",
    ports: "#ports",
    contract: "#contract",
  };

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

  const injectNavigationStyles = () => {
    if (document.getElementById("freight-nav-polish")) return;

    const style = document.createElement("style");
    style.id = "freight-nav-polish";
    style.textContent = `
      html {
        scroll-behavior: smooth;
      }

      #overview,
      #forecast,
      #vessels,
      #ports,
      #contract {
        scroll-margin-top: 22px;
        transition:
          transform 220ms ease,
          box-shadow 220ms ease,
          border-color 220ms ease;
        will-change: transform;
      }

      .freight-nav-active {
        color: #f3f7f9 !important;
        background: #1a252d !important;
        box-shadow: inset 3px 0 0 #e4ef37, 0 6px 18px rgba(16, 23, 29, 0.08);
      }

      .freight-nav-focus {
        transform: translateY(-5px);
        box-shadow:
          0 14px 34px rgba(16, 24, 30, 0.12),
          0 0 0 1px rgba(228, 239, 55, 0.28);
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

  const setActive = (id, pulse = false) => {
    document.querySelectorAll(".sidebar nav a[href]").forEach((link) => {
      const target = link.getAttribute("href");
      const isActive = target === `#${id}`;

      // Remove the React hard-coded `active` state so only one item can be selected.
      link.classList.remove("active");
      link.classList.toggle("freight-nav-active", isActive);

      if (isActive) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });

    if (!pulse) return;

    const target = document.getElementById(id);
    if (!target) return;

    target.classList.remove("freight-nav-focus");
    requestAnimationFrame(() => {
      target.classList.add("freight-nav-focus");
      window.setTimeout(() => {
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
      .filter((item) => item.element)
      .sort((a, b) =>
        a.element.getBoundingClientRect().top -
        b.element.getBoundingClientRect().top
      );

  const updateActiveFromScroll = () => {
    const sections = getSections();
    if (!sections.length) return;

    // The section whose top has most recently crossed this guide line is active.
    // This handles the nested #ports section inside #forecast correctly.
    const guideLine = window.innerHeight * 0.28;
    let active = sections[0];

    for (const section of sections) {
      if (section.element.getBoundingClientRect().top <= guideLine) {
        active = section;
      } else {
        break;
      }
    }

    setActive(active.id);
  };

  const scheduleScrollActiveUpdate = () => {
    if (scrollHandler) return;

    scrollHandler = requestAnimationFrame(() => {
      scrollHandler = null;
      updateActiveFromScroll();
    });
  };

  const setupNavigation = () => {
    if (navigationScheduled) return;
    navigationScheduled = true;

    requestAnimationFrame(() => {
      navigationScheduled = false;
      injectNavigationStyles();

      const navLinks = document.querySelectorAll(".sidebar nav a[href]");
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

          setActive(id, true);
          target.scrollIntoView({ behavior: "smooth", block: "start" });

          if (window.history?.replaceState) {
            window.history.replaceState(null, "", href);
          }

          link.blur();
        });
      });

      window.removeEventListener("scroll", scheduleScrollActiveUpdate);
      window.addEventListener("scroll", scheduleScrollActiveUpdate, {
        passive: true,
      });
      window.addEventListener("resize", scheduleScrollActiveUpdate, {
        passive: true,
      });

      const hash = window.location.hash.slice(1);
      if (hash && navMap[hash]) {
        setActive(hash);
      } else {
        updateActiveFromScroll();
      }
    });
  };

  const refreshLabels = () => {
    if (refreshScheduled) return;
    refreshScheduled = true;

    requestAnimationFrame(() => {
      refreshScheduled = false;
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
  injectNavigationStyles();
  setupNavigation();
  refreshLabels();

  observer = new MutationObserver(() => {
    setupNavigation();
    refreshLabels();
  });

  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    characterData: true,
  });
})();
