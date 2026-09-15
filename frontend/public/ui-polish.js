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

  const refresh = () => {
    if (scheduled) return;
    scheduled = true;

    requestAnimationFrame(() => {
      scheduled = false;
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

  new MutationObserver(refresh).observe(document.documentElement, {
    subtree: true,
    childList: true,
    characterData: true,
  });

  refresh();
})();
