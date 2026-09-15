(() => {
  const MODEL_CLASSES = ["HSI", "SI", "PI", "CI"];
  let refreshScheduled = false;
  let navigationScheduled = false;
  let observer;
  let intersectionObserver;

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
      link.classList.toggle("freight-nav-active", target === `#${id}`);
      if (target === `#${id}`) {
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

  const setupIntersectionObserver = () => {
    const sections = Object.entries(navMap)
      .map(([id, selector]) => ({ id, element: document.querySelector(selector) }))
      .filter((item) => item.element);

    if (!sections.length || typeof IntersectionObserver === "undefined") return;

    intersectionObserver?.disconnect();
    intersectionObserver = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio);

        if (visible[0]) {
          setActive(visible[0].target.id);
        }
      },
      {
        root: null,
        rootMargin: "-18% 0px -62% 0px",
        threshold: [0.08, 0.2, 0.45],
      }
    );

    sections.forEach(({ element }) => intersectionObserver.observe(element));
  };

  const setupNavigation = () => {
    if (navigationScheduled) return;
    navigationScheduled = true;

    requestAnimationFrame(() => {
      navigationScheduled = false;
      injectNavigationStyles();
      setupIntersectionObserver();

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
          setActive(href.slice(1), true);
          target.scrollIntoView({ behavior: "smooth", block: "start" });

          if (window.history?.replaceState) {
            window.history.replaceState(null, "", href);
          }

          link.blur();
        });
      });

      const hash = window.location.hash.slice(1);
      if (hash && navMap[hash]) setActive(hash);
      else setActive("overview");
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
