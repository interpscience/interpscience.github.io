(() => {
  const header = document.querySelector("[data-header]");
  const toggle = document.querySelector("[data-nav-toggle]");
  const mobileNav = document.querySelector("[data-mobile-nav]");

  const onScroll = () => {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 24);
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  if (toggle && mobileNav) {
    toggle.addEventListener("click", () => {
      const open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      mobileNav.hidden = open;
    });

    mobileNav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        toggle.setAttribute("aria-expanded", "false");
        mobileNav.hidden = true;
      });
    });
  }

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  initConstellation(reduceMotion);

  const reveals = document.querySelectorAll("[data-reveal]");

  if (reduceMotion || !("IntersectionObserver" in window)) {
    reveals.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.12 }
  );

  reveals.forEach((el) => observer.observe(el));
})();

function initConstellation(reduceMotion) {
  const lines = [...document.querySelectorAll(".constellation .line")];
  const nodes = [...document.querySelectorAll(".nodes .node")];
  if (!lines.length) return;

  if (reduceMotion) {
    lines.forEach((line) => {
      line.style.strokeDasharray = "none";
      line.style.strokeDashoffset = "0";
    });
    nodes.forEach((node) => node.classList.add("is-visible"));
    return;
  }

  const unused = new Set(nodes);

  const distanceAlongPath = (path, x, y) => {
    const total = path.getTotalLength();
    if (total === 0) return { length: 0, dist2: Infinity };
    let best = 0;
    let bestDist = Infinity;
    const steps = Math.max(32, Math.ceil(total / 2));
    for (let i = 0; i <= steps; i += 1) {
      const len = (total * i) / steps;
      const pt = path.getPointAtLength(len);
      const d = (pt.x - x) ** 2 + (pt.y - y) ** 2;
      if (d < bestDist) {
        bestDist = d;
        best = len;
      }
    }
    return { length: best, dist2: bestDist };
  };

  const DRAW_MS = 1600;
  const DRAW_DELAY_MS = 250;
  const NODE_HIT_PX2 = 16 * 16;
  const ease = "cubic-bezier(0.22, 1, 0.36, 1)";

  lines.forEach((line) => {
    const total = line.getTotalLength();
    line.style.strokeDasharray = String(total);
    line.style.strokeDashoffset = String(total);
    line.style.animation = "none";

    const arrivals = [];
    unused.forEach((node) => {
      const x = Number(node.getAttribute("cx"));
      const y = Number(node.getAttribute("cy"));
      const hit = distanceAlongPath(line, x, y);
      if (hit.dist2 <= NODE_HIT_PX2) {
        arrivals.push({
          node,
          at: hit.length / total,
          atLen: hit.length,
          x,
          y,
        });
        unused.delete(node);
      }
    });

    arrivals.sort((a, b) => a.at - b.at);
    const settled = new Set();

    const place = (node, x, y, traveling) => {
      node.setAttribute("cx", String(x));
      node.setAttribute("cy", String(y));
      node.classList.add("is-visible");
      node.classList.toggle("is-traveling", traveling);
    };

    const settle = (item) => {
      if (settled.has(item.node)) return;
      settled.add(item.node);
      place(item.node, item.x, item.y, false);
    };

    const syncNodes = () => {
      const offset = parseFloat(getComputedStyle(line).strokeDashoffset);
      if (Number.isNaN(offset)) return;
      // Draw hasn't started while offset is still at full length
      if (offset >= total - 0.5) return;

      const tipLen = Math.max(0, Math.min(total, total - offset));

      arrivals.forEach((item, i) => {
        const prevLen = i === 0 ? 0 : arrivals[i - 1].atLen;

        if (tipLen < prevLen - 0.5) return;

        if (item.atLen <= 0.5 || tipLen >= item.atLen) {
          settle(item);
          return;
        }

        const travelLen = Math.max(prevLen, tipLen);
        const pt = line.getPointAtLength(travelLen);
        place(item.node, pt.x, pt.y, true);
      });
    };

    const anim = line.animate(
      [{ strokeDashoffset: total }, { strokeDashoffset: 0 }],
      {
        duration: DRAW_MS,
        delay: DRAW_DELAY_MS,
        easing: ease,
        fill: "forwards",
      }
    );

    const tick = () => {
      syncNodes();
      if (anim.playState === "finished") {
        arrivals.forEach(settle);
        return;
      }
      if (anim.playState === "running" || anim.playState === "pending") {
        requestAnimationFrame(tick);
      }
    };

    requestAnimationFrame(tick);
    anim.finished
      .then(() => {
        arrivals.forEach(settle);
      })
      .catch(() => {});
  });

  unused.forEach((node, i) => {
    window.setTimeout(
      () => node.classList.add("is-visible"),
      DRAW_DELAY_MS + DRAW_MS * 0.8 + i * 70
    );
  });
}

