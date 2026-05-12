/**
 * Library AI Chatbot — Inline Embed for Koha OPACUserJS
 */
(function () {
  "use strict";
  var CHATBOT_API = "/chatbot";
  // Auto-detect: when served from Vercel, use same origin (empty string = relative).
  // When embedded on an external site (like Koha), use the script's own origin.
  if (window.location.hostname.includes("vercel.app")) {
    CHATBOT_API = "";
  } else {
    // Detect the origin from the script tag's src attribute
    try {
      var scripts = document.getElementsByTagName("script");
      for (var i = scripts.length - 1; i >= 0; i--) {
        var src = scripts[i].src || "";
        if (src.indexOf("koha-chatbot-inline") !== -1) {
          CHATBOT_API = src.replace(/\/static\/koha-chatbot-inline\.js.*$/, "");
          break;
        }
      }
    } catch (e) {}
  }
  // Don't init inside iframes that we created (prevents infinite nesting)
  // but allow init on normal Koha pages even if they happen to be framed
  try {
    if (window !== window.top && window.frameElement && window.frameElement.id === "lc-detail-frame") return;
  } catch(e) {}
  if (document.getElementById("lc-fab")) return;

  var css = document.createElement("style");
  css.textContent =
    "#lc-fab{position:fixed;bottom:24px;right:24px;z-index:100000;" +
    "width:60px;height:60px;border-radius:50%;background:#0E553F;color:#fff;" +
    "border:3px solid #D4A017;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.3);" +
    "font-size:28px;display:flex;align-items:center;justify-content:center;" +
    "transition:transform .2s,background .2s;overflow:hidden;padding:0}" +
    "#lc-fab:hover{background:#0a3f2e;transform:scale(1.08)}" +
    "#lc-fab-avatar{width:100%;height:100%;object-fit:cover;border-radius:50%;display:block}" +
    "#lc-fab-close{font-size:22px;color:#fff;line-height:1;display:none}" +
    "#lc-fab.open #lc-fab-avatar{display:none}" +
    "#lc-fab.open #lc-fab-close{display:block}" +
    "#lc-wrap{position:fixed;bottom:92px;right:24px;z-index:99999;" +
    "width:400px;height:560px;max-width:calc(100vw - 32px);" +
    "max-height:calc(100vh - 120px);border-radius:12px;overflow:hidden;" +
    "box-shadow:0 8px 32px rgba(0,0,0,.2);display:none;background:#fff;" +
    "flex-direction:column;font-family:-apple-system,BlinkMacSystemFont," +
    "'Segoe UI',Roboto,Helvetica,Arial,sans-serif}" +
    "#lc-wrap.open{display:flex}" +
    "#lc-hdr{background:#0E553F;color:#fff;padding:10px 14px;" +
    "font-size:1.05rem;font-weight:600;display:flex;align-items:center;" +
    "gap:10px;flex-shrink:0}" +
    "#lc-hdr-avatar{width:38px;height:38px;border-radius:50%;border:2px solid #D4A017;" +
    "object-fit:cover;flex-shrink:0;background:#0a3f2e}" +
    "#lc-new{background:none;border:1px solid rgba(255,255,255,.4);color:#fff;" +
    "border-radius:14px;padding:4px 12px;font-size:.75rem;cursor:pointer;" +
    "margin-left:auto;transition:background .15s}" +
    "#lc-new:hover{background:rgba(255,255,255,.15)}" +
    "#lc-msgs{flex:1;overflow-y:auto;padding:14px;display:flex;" +
    "flex-direction:column;gap:8px;background:#fff}" +
    ".lc-m{max-width:80%;padding:10px 14px;border-radius:16px;" +
    "font-size:.93rem;line-height:1.45;word-wrap:break-word;white-space:pre-wrap}" +
    ".lc-m.u{align-self:flex-end;background:#0E553F;color:#fff;" +
    "border-bottom-right-radius:4px}" +
    ".lc-m.b{align-self:flex-start;background:#f0f0ec;color:#2d2d2d;" +
    "border-bottom-left-radius:4px}" +
    ".lc-m img{display:block;max-width:100%;height:auto;border-radius:8px;" +
    "margin-top:8px;cursor:pointer}" +
    ".lc-img-wrap{margin-top:8px;width:100%;overflow:hidden}" +
    ".lc-img-link{font-size:.82rem;color:#0E553F;text-decoration:underline;" +
    "cursor:pointer;display:block;margin-bottom:4px}" +
    ".lc-fb{display:none}" +
    ".lc-handoff-rate{display:flex;gap:8px;justify-content:center}" +
    ".lc-rate-btn{background:#fff;border:1px solid #ccc;border-radius:18px;" +
    "padding:8px 16px;font-size:.88rem;cursor:pointer;transition:all .15s}" +
    ".lc-rate-btn:hover{border-color:#0E553F;background:#f0fdf4}" +
    ".lc-m.e{align-self:center;background:#fce4e4;color:#a94442;" +
    "border-radius:8px;font-size:.85rem;text-align:center}" +
    ".lc-t{align-self:flex-start;display:flex;align-items:center;gap:8px;padding:10px 14px;" +
    "background:#f0f0ec;border-radius:16px;border-bottom-left-radius:4px;color:#888;font-size:.82rem}" +
    ".lc-spinner{width:18px;height:18px;border:2.5px solid #ddd;border-top-color:#D4A017;" +
    "border-radius:50%;animation:lcSpin .7s linear infinite}" +
    "@keyframes lcSpin{to{transform:rotate(360deg)}}" +
    "#lc-bar{display:flex;padding:10px;gap:8px;border-top:1px solid #e0e0e0;" +
    "background:#fff;flex-shrink:0}" +
    "#lc-in{flex:1;padding:10px 14px;border:1px solid #ccc;border-radius:20px;" +
    "font-size:.93rem;outline:none;text-align:left}" +
    "#lc-in:focus{border-color:#0E553F}" +
    "#lc-go{background:#D4A017;color:#fff;border:none;border-radius:50%;" +
    "width:40px;height:40px;cursor:pointer;display:flex;align-items:center;" +
    "justify-content:center;font-size:1.1rem;flex-shrink:0}" +
    "#lc-go:hover{background:#b8890f}" +
    "#lc-go:disabled{background:#a0aab4;cursor:not-allowed}" +
    ".lc-w{text-align:center;color:#555;font-size:.88rem;padding:18px 10px;" +
    "line-height:1.5}" +
    ".lc-faqs{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;padding:8px 10px 14px}" +
    ".lc-faq{background:#fff;color:#0E553F;border:1px solid #D4A017;border-radius:18px;" +
    "padding:7px 14px;font-size:.82rem;cursor:pointer;transition:background .15s,border-color .15s;" +
    "line-height:1.3;text-align:left}" +
    ".lc-faq:hover{background:#fdf6e3;border-color:#b8890f}" +
    // Catalog result cards
    ".lc-results{display:flex;flex-direction:column;gap:8px;width:100%;max-width:95%;align-self:flex-start}" +
    ".lc-results-header{font-size:.88rem;color:#555;padding:4px 0}" +
    ".lc-card{background:#fff;border:1px solid #e0e0e0;border-radius:10px;padding:10px 12px;" +
    "display:flex;flex-direction:column;gap:6px;transition:border-color .15s}" +
    ".lc-card:hover{border-color:#0E553F}" +
    ".lc-card-title{font-size:.88rem;font-weight:600;color:#2d2d2d;line-height:1.3}" +
    ".lc-card-author{font-size:.78rem;color:#666}" +
    ".lc-card-btn{display:inline-block;background:#0E553F!important;color:#fff!important;border:none;border-radius:14px;" +
    "padding:5px 14px;font-size:.76rem;cursor:pointer;text-decoration:none!important;" +
    "text-align:center;transition:background .15s;align-self:flex-start}" +
    ".lc-card-btn:hover{background:#0a3f2e!important}" +
    ".lc-pager{display:flex;flex-direction:column;align-items:center;gap:4px;padding:6px 0}" +
    ".lc-pager-row{display:flex;align-items:center;gap:6px}" +
    ".lc-pager-btn{background:#fff;border:1px solid #ccc;border-radius:14px;" +
    "padding:4px 12px;font-size:.78rem;cursor:pointer;color:#0E553F;transition:all .15s}" +
    ".lc-pager-btn:hover{background:#f0fdf4;border-color:#0E553F}" +
    ".lc-pager-btn:disabled{opacity:.4;cursor:default;background:#fff}" +
    ".lc-pager-btn.active{background:#0E553F;color:#fff;border-color:#0E553F}" +
    ".lc-pager-info{font-size:.75rem;color:#888}" +
    "#lc-librarian{background:none;border:1px solid rgba(255,255,255,.4);color:#fff;" +
    "border-radius:14px;padding:4px 10px;font-size:.72rem;cursor:pointer;" +
    "transition:background .15s;white-space:nowrap}" +
    "#lc-librarian:hover:not(:disabled){background:rgba(255,255,255,.15)}" +
    "#lc-librarian:disabled{opacity:.45;cursor:not-allowed;border-color:rgba(255,255,255,.2)}" +
    "@media(max-width:480px){#lc-wrap{bottom:0;right:0;width:100vw;" +
    "height:100vh;max-width:100vw;max-height:100vh;border-radius:0}" +
    "#lc-fab{bottom:16px;right:16px}}";
  document.head.appendChild(css);

  // Avatar URL — DiceBear avataaars, librarian style matching green/gold theme
  var AVATAR_URL = "https://api.dicebear.com/7.x/avataaars/svg?seed=LLORA&backgroundColor=0e553f" +
    "&top=straight01&accessories=prescription02&eyes=happy" +
    "&eyebrows=default&mouth=smile&clothing=blazerAndShirt&style=circle";

  // FAB
  var fab = document.createElement("button");
  fab.id = "lc-fab";
  fab.setAttribute("aria-label", "Open library chat assistant");
  fab.innerHTML =
    '<img id="lc-fab-avatar" src="' + AVATAR_URL + '" alt="LLORA avatar" />' +
    '<span id="lc-fab-close" aria-hidden="true">&#10005;</span>';
  document.body.appendChild(fab);

  // Chat panel
  var wrap = document.createElement("div");
  wrap.id = "lc-wrap";
  wrap.setAttribute("role", "dialog");
  wrap.setAttribute("aria-label", "Library chat assistant");
  wrap.innerHTML =
    '<div id="lc-hdr"><img id="lc-hdr-avatar" src="' + AVATAR_URL + '" alt="LLORA avatar" /> LLORA — Library Assistant<button id="lc-librarian" aria-label="Talk to a librarian">&#128172; Librarian</button><button id="lc-new" aria-label="Start new chat">New Chat</button></div>' +
    '<div id="lc-msgs" role="log" aria-live="polite">' +
    '<div class="lc-w">Hello, I\'m LLORA (Lorma Library Online Research Assistant), your virtual assistant. I\'m here to provide the assistance you need. I\'ll be happy to serve you.</div>' +
    '<div class="lc-faqs" id="lc-faqs-init">' +
    '</div>' +
    '</div>' +
    '<div id="lc-bar">' +
    '<input type="text" id="lc-in" placeholder="Ask me about the library..." autocomplete="off" aria-label="Type your message">' +
    '<button id="lc-go" aria-label="Send message" disabled>&#10148;</button>' +
    '</div>';
  document.body.appendChild(wrap);

  var msgs = document.getElementById("lc-msgs");
  var inp = document.getElementById("lc-in");
  var btn = document.getElementById("lc-go");

  // Session — persist across page navigations
  var STORE_KEY = "lc_chat";
  var STORE_VER = 3; // bump to clear stale data
  var stored = {};
  try {
    var raw = JSON.parse(sessionStorage.getItem(STORE_KEY)) || {};
    if (raw.ver === STORE_VER) stored = raw;
  } catch(e) {}
  var sid = stored.sid || ((typeof crypto !== "undefined" && crypto.randomUUID)
    ? crypto.randomUUID()
    : "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
        var r = (Math.random() * 16) | 0;
        return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
      }));
  var chatHistory = stored.history || []; // [{text, cls}]
  var wasOpen = stored.open !== undefined ? stored.open : true;
  // Patron identity — persisted so returning users skip the form
  var _patronType    = stored.patronType    || "";
  var _patronDetails = stored.patronDetails || "";

  function saveState() {
    try {
      sessionStorage.setItem(STORE_KEY, JSON.stringify({
        ver: STORE_VER, sid: sid, history: chatHistory.slice(-40), open: open,
        patronType: _patronType, patronDetails: _patronDetails
      }));
    } catch(e) {}
  }

  // FAQ buttons — loaded from server
  function buildFaqHtml(faqs) {
    if (!faqs || faqs.length === 0) return "";
    return faqs.map(function(f) {
      return '<button class="lc-faq" data-q="' + f.question.replace(/"/g, "&quot;") + '">' + f.label + '</button>';
    }).join("");
  }
  var _FAQ_FALLBACK = [
    { label: "&#128336; Library Hours", question: "What are the library hours?" },
    { label: "&#128172; LIBVAS", question: "What is LIBVAS?" },
    { label: "&#128196; LIBRS", question: "What is LIBRS?" },
    { label: "&#128187; LIBRAS", question: "What is LIBRAS?" },
    { label: "&#128424; LibPrintS", question: "How does LibPrintS work?" }
  ];

  function loadAndRenderFaqs(container) {
    // Retry up to 3 times to handle Vercel cold-start empty responses
    var attempts = 0;
    function tryFetch() {
      fetch(CHATBOT_API + "/api/faqs?t=" + Date.now())
        .then(function(r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          return r.json();
        })
        .then(function(d) {
          var faqs = d.faqs || [];
          if (faqs.length === 0 && attempts < 2) {
            // Empty response — may be cold-start, retry after 1.5s
            attempts++;
            setTimeout(tryFetch, 1500);
            return;
          }
          container.innerHTML = buildFaqHtml(faqs.length > 0 ? faqs : _FAQ_FALLBACK);
        })
        .catch(function() {
          if (attempts < 2) {
            attempts++;
            setTimeout(tryFetch, 1500);
          } else {
            container.innerHTML = buildFaqHtml(_FAQ_FALLBACK);
          }
        });
    }
    tryFetch();
  }

  // Load FAQs into the initial welcome screen, but keep hidden until identity is done
  var initFaqContainer = document.getElementById("lc-faqs-init");
  if (initFaqContainer) loadAndRenderFaqs(initFaqContainer);

  // Load AI config (name + welcome message) from server
  var AFTER_HOURS_MESSAGE = (
    "Hello! Our librarians are currently offline. 🕐\n\n" +
    "Please note your questions and ask a librarian during active hours. " +
    "In the meantime, I'm LLORA and I'll do my best to answer your questions. 📚"
  );

  fetch(CHATBOT_API + "/api/ai-config?t=" + Date.now())
    .then(function(r) { return r.json(); })
    .then(function(d) {
      var name = d.name || "LLORA";
      var welcome = d.welcome_message || ("Hello, I'm " + name + " (Lorma Library Online Research Assistant), your virtual assistant. I'm here to provide the assistance you need. I'll be happy to serve you.");
      // Replace LLORA placeholder in after-hours message with actual bot name
      AFTER_HOURS_MESSAGE = AFTER_HOURS_MESSAGE.replace("LLORA", name);
      // Update header
      var hdr = document.getElementById("lc-hdr");
      if (hdr) {
        // Update the text node that follows the avatar image
        hdr.childNodes.forEach(function(n) {
          if (n.nodeType === 3 && n.textContent.trim()) {
            n.textContent = " " + name + " — Library Assistant";
          }
        });
      }
      // Always show normal welcome + FAQs regardless of library hours
      var wEl = msgs.querySelector(".lc-w");
      if (wEl) wEl.textContent = welcome;
    })
    .catch(function() {});

  // Restore previous messages — skip librarian poll messages (they start with "👩‍💼 Librarian:")
  // because the poll will re-fetch them fresh from the DB, avoiding duplicates.
  if (chatHistory.length > 0) {
    var w = msgs.querySelector(".lc-w"); if (w) w.remove();
    var fq = msgs.querySelector(".lc-faqs"); if (fq) fq.remove();
    chatHistory.forEach(function(m) {
      if (m.cls === "b" && m.text && m.text.indexOf("👩‍💼 Librarian:") === 0) return;
      addMsgRaw(m.text, m.cls, m.ts, m.imgUrl || null, m.pdfUrl || null);
    });
  }

  // Check if the existing session has expired — auto-reset to new chat
  if (chatHistory.length > 0 && sid) {
    fetch(CHATBOT_API + "/api/session-status/" + encodeURIComponent(sid))
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (d.status === "expired" || d.status === "not_found") {
          resetToNewChat();
        }
      })
      .catch(function() {});
  }

  // Toggle — restore previous state
  var open = wasOpen;
  if (open) {
    wrap.classList.add("open");
    fab.classList.add("open");
    fab.setAttribute("aria-label", "Close chat");
  }

  // Scroll to bottom after everything is rendered and visible
  if (chatHistory.length > 0 && open) {
    // Multiple attempts to ensure scroll works across all browsers
    function scrollToBottom() { msgs.scrollTop = msgs.scrollHeight; }
    scrollToBottom();
    setTimeout(scrollToBottom, 100);
    setTimeout(scrollToBottom, 300);
    window.addEventListener("load", scrollToBottom);
  }
  fab.addEventListener("click", function () {
    open = !open;
    wrap.classList.toggle("open", open);
    fab.classList.toggle("open", open);
    fab.setAttribute("aria-label", open ? "Close chat" : "Open library chat assistant");
    if (open) {
      // Show identity form on first open if not yet identified
      if (!_identityDone) {
        _lockChat();
        showPatronTypeStep();
        _identityDone = true; // prevent showing again on re-open
      } else {
        inp.focus();
      }
      setTimeout(function() { msgs.scrollTop = msgs.scrollHeight; }, 50);
    }
    saveState();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && open) {
      open = false; wrap.classList.remove("open");
      fab.classList.remove("open");
      fab.setAttribute("aria-label", "Open library chat assistant");
      fab.focus();
    }
  });

  // Helpers
  function scroll() { msgs.scrollTop = msgs.scrollHeight; }
  function renderMsg(t, c, ts, imgUrl, pdfUrl) {
    var d = document.createElement("div"); d.className = "lc-m " + c;
    // Check if this is a catalog result message — render as cards
    if (c === "b" && t && t.indexOf("found in the catalog") !== -1) {
      return renderCatalogCards(t, ts);
    }
    // Only render text if there is text content
    if (t && t.trim()) {
      var html = t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      // Render markdown links [text](url) — only for http/https URLs
      html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g,
        '<a href="$2" class="lc-link" style="color:inherit;text-decoration:underline;cursor:pointer" target="_blank" rel="noopener">$1</a>');
      // Render bare URLs
      html = html.replace(/(^|[^"'=])(https?:\/\/[^\s<&]+)/g,
        '$1<a href="$2" class="lc-link" style="color:inherit;text-decoration:underline;cursor:pointer" target="_blank" rel="noopener">$2</a>');
      // Preserve line breaks
      html = html.replace(/\n/g, "<br>");
      d.innerHTML = html;
    }
    // Render image if provided
    if (imgUrl && c === "b") {
      // Make relative URLs absolute using the chatbot API base
      var resolvedImgUrl = imgUrl;
      if (imgUrl.startsWith("/")) {
        resolvedImgUrl = CHATBOT_API + imgUrl;
      }
      var imgWrap = document.createElement("div");
      imgWrap.className = "lc-img-wrap";
      // Always show a clickable link first (guaranteed visible)
      var imgLink = document.createElement("a");
      imgLink.href = resolvedImgUrl;
      imgLink.target = "_blank";
      imgLink.rel = "noopener";
      imgLink.textContent = "View image";
      imgLink.className = "lc-img-link";
      imgLink.addEventListener("click", function(e) { e.stopPropagation(); });
      imgWrap.appendChild(imgLink);
      // Also try to render inline
      var img = document.createElement("img");
      img.alt = "Reply image";
      img.addEventListener("load", function() {
        // Image loaded — hide the text link since image is visible
        imgLink.style.display = "none";
        scroll();
      });
      img.addEventListener("error", function() {
        // Image failed — keep the text link, hide broken img
        img.style.display = "none";
      });
      img.addEventListener("click", function() { window.open(resolvedImgUrl, "_blank"); });
      img.src = resolvedImgUrl;
      imgWrap.appendChild(img);
      d.appendChild(imgWrap);
    }
    // Render PDF download button if provided
    if (pdfUrl && c === "b") {
      var resolvedPdfUrl = pdfUrl;
      if (pdfUrl.startsWith("/")) {
        resolvedPdfUrl = CHATBOT_API + pdfUrl;
      }
      var pdfBtn = document.createElement("a");
      pdfBtn.href = resolvedPdfUrl;
      pdfBtn.target = "_blank";
      pdfBtn.rel = "noopener";
      pdfBtn.style.cssText = "display:inline-flex;align-items:center;gap:6px;margin-top:10px;" +
        "background:#0E553F;color:#fff;border-radius:14px;padding:7px 14px;" +
        "font-size:.82rem;text-decoration:none;font-weight:600;transition:background .15s";
      pdfBtn.innerHTML = "&#128196; Download PDF";
      pdfBtn.addEventListener("mouseover", function() { this.style.background = "#0a3f2e"; });
      pdfBtn.addEventListener("mouseout", function() { this.style.background = "#0E553F"; });
      pdfBtn.addEventListener("click", function(e) { e.stopPropagation(); });
      d.appendChild(pdfBtn);
    }
    d.querySelectorAll("a.lc-link").forEach(function(a) {
      a.addEventListener("click", function(e) {
        e.preventDefault();
        e.stopPropagation();
        window.location.href = a.href;
      });
    });
    return d;
  }
  function renderCatalogCards(text, ts) {
    var d = document.createElement("div"); d.className = "lc-m b";
    d.style.cssText = "max-width:80%;white-space:normal";
    var wrap = document.createElement("div"); wrap.className = "lc-results";
    wrap.style.cssText = "width:100%";
    var lines = text.split("\n");
    var headerDiv = document.createElement("div"); headerDiv.className = "lc-results-header";
    headerDiv.textContent = "📚 Here's what I found in the catalog:";
    wrap.appendChild(headerDiv);

    // Parse all cards from text
    var allCards = [];
    var currentTitle = "", currentAuthor = "", currentUrl = "";
    function collectCard() {
      if (!currentTitle) return;
      allCards.push({ title: currentTitle, author: currentAuthor, url: currentUrl });
      currentTitle = ""; currentAuthor = ""; currentUrl = "";
    }
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i].trim();
      var numMatch = line.match(/^\d+\.\s+(.+?)(?:\s+by\s+(.+))?$/);
      if (numMatch && line.indexOf("View in catalog") === -1) {
        collectCard();
        currentTitle = numMatch[1] || "";
        currentAuthor = numMatch[2] || "";
        if (!currentAuthor && currentTitle.match(/\s+by\s*$/)) {
          currentTitle = currentTitle.replace(/\s+by\s*$/, "");
        }
      } else if (line.indexOf("View in catalog:") !== -1) {
        var urlMatch = line.match(/https?:\/\/[^\s]+/);
        if (urlMatch) currentUrl = urlMatch[0];
      }
    }
    collectCard();

    // Pagination
    var PAGE_SIZE = 3;
    var currentPage = 0;
    var totalPages = Math.ceil(allCards.length / PAGE_SIZE);

    var cardsContainer = document.createElement("div");
    cardsContainer.style.cssText = "display:flex;flex-direction:column;gap:8px";
    wrap.appendChild(cardsContainer);

    var pagerDiv = document.createElement("div"); pagerDiv.className = "lc-pager";
    if (totalPages > 1) wrap.appendChild(pagerDiv);

    function renderPage() {
      cardsContainer.innerHTML = "";
      var start = currentPage * PAGE_SIZE;
      var end = Math.min(start + PAGE_SIZE, allCards.length);
      for (var j = start; j < end; j++) {
        var rec = allCards[j];
        var card = document.createElement("div"); card.className = "lc-card";
        var titleEl = document.createElement("div"); titleEl.className = "lc-card-title";
        titleEl.textContent = rec.title;
        card.appendChild(titleEl);
        if (rec.author) {
          var authorEl = document.createElement("div"); authorEl.className = "lc-card-author";
          authorEl.textContent = "by " + rec.author;
          card.appendChild(authorEl);
        }
        if (rec.url) {
          var btn = document.createElement("a"); btn.className = "lc-card-btn";
          btn.href = rec.url; btn.textContent = "View in catalog";
          btn.addEventListener("click", function(e) { e.stopPropagation(); });
          card.appendChild(btn);
        }
        cardsContainer.appendChild(card);
      }
      // Update pager
      if (totalPages > 1) {
        pagerDiv.innerHTML = "";
        var row = document.createElement("div"); row.className = "lc-pager-row";
        var prev = document.createElement("button"); prev.className = "lc-pager-btn";
        prev.textContent = "◀"; prev.disabled = currentPage === 0;
        prev.addEventListener("click", function() { if (currentPage > 0) { currentPage--; renderPage(); scroll(); } });
        row.appendChild(prev);
        // Sliding window: show max 5 page numbers around current page
        var maxVisible = 5;
        var half = Math.floor(maxVisible / 2);
        var startPage = Math.max(0, currentPage - half);
        var endPage = Math.min(totalPages, startPage + maxVisible);
        if (endPage - startPage < maxVisible) startPage = Math.max(0, endPage - maxVisible);
        for (var p = startPage; p < endPage; p++) {
          (function(pg) {
            var numBtn = document.createElement("button"); numBtn.className = "lc-pager-btn";
            numBtn.textContent = pg + 1;
            if (pg === currentPage) numBtn.classList.add("active");
            numBtn.addEventListener("click", function() { currentPage = pg; renderPage(); scroll(); });
            row.appendChild(numBtn);
          })(p);
        }
        var next = document.createElement("button"); next.className = "lc-pager-btn";
        next.textContent = "▶"; next.disabled = currentPage === totalPages - 1;
        next.addEventListener("click", function() { if (currentPage < totalPages - 1) { currentPage++; renderPage(); scroll(); } });
        row.appendChild(next);
        pagerDiv.appendChild(row);
        var info = document.createElement("span"); info.className = "lc-pager-info";
        info.textContent = (start + 1) + "–" + end + " of " + allCards.length;
        pagerDiv.appendChild(info);
      }
    }
    renderPage();

    d.appendChild(wrap);
    return d;
  }
  function addMsgRaw(t, c, ts, imgUrl, pdfUrl) {
    msgs.appendChild(renderMsg(t, c, ts, imgUrl, pdfUrl)); scroll();
  }
  function addMsg(t, c, ts, imgUrl, pdfUrl) {
    addMsgRaw(t, c, ts, imgUrl, pdfUrl);
    chatHistory.push({text: t, cls: c, ts: ts, imgUrl: imgUrl || null, pdfUrl: pdfUrl || null});
    saveState();
    resetInactivityTimer();
  }
  function showTyping(label) {
    var d = document.createElement("div"); d.className = "lc-t"; d.id = "lc-tp";
    d.innerHTML = '<div class="lc-spinner"></div> ' + (label || 'Thinking…');
    msgs.appendChild(d); scroll();
  }
  function hideTyping() { var e = document.getElementById("lc-tp"); if (e) e.remove(); }

  // Input
  var lastTypingSignal = 0;
  inp.addEventListener("input", function () {
    btn.disabled = !inp.value.trim();
    // Send typing signal during live chat
    if (handoffActive && handoffHandler && inp.value.trim()) {
      var now = Date.now();
      if (now - lastTypingSignal > 1500) {
        lastTypingSignal = now;
        fetch(CHATBOT_API + "/api/typing/" + encodeURIComponent(sid), { method: "POST" }).catch(function(){});
      }
    }
  });
  inp.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !btn.disabled) { e.preventDefault(); send(); }
  });
  btn.addEventListener("click", send);

  // FAQ buttons — auto-send the question
  msgs.addEventListener("click", function (e) {
    var target = e.target;
    // Handle click on FAQ buttons or Talk to Librarian button
    var faq = target.closest ? target.closest(".lc-faq") : null;
    if (!faq && target.classList && target.classList.contains("lc-faq")) faq = target;
    if (!faq) return;
    e.preventDefault();
    e.stopPropagation();
    var question = faq.getAttribute("data-q");
    if (!question) return;
    inp.value = question;
    btn.disabled = false;
    send();
  });

  // Talk to a Librarian header button — triggers handoff via chat
  var libBtn = document.getElementById("lc-librarian");
  var libBtnAvailable = true; // tracks current availability state

  function setLibrarianButtonState(available, reason) {
    libBtnAvailable = available;
    // Don't touch the DOM button if the identity form is still pending —
    // _lockChat() owns the disabled state until identity is complete.
    // We still update libBtnAvailable so _unlockChat() uses the correct value.
    if (!_patronType) return;
    // Always keep the button enabled so it can be clicked to show the offline message.
    // Visual state changes to indicate availability without blocking interaction.
    libBtn.disabled = false;
    if (available) {
      libBtn.style.opacity = "1";
      libBtn.style.cursor = "pointer";
      libBtn.title = "";
    } else {
      libBtn.style.opacity = "0.6";
      libBtn.style.cursor = "pointer";
      libBtn.title = reason || "Librarian chat is currently unavailable.";
    }
  }

  function checkLibrarianAvailability() {
    fetch(CHATBOT_API + "/api/librarian-available?t=" + Date.now())
      .then(function(r) { return r.json(); })
      .then(function(d) {
        // Only update state if we got a valid response with an explicit available field
        if (typeof d.available === "boolean" && !handoffActive) {
          setLibrarianButtonState(d.available, d.reason);
        }
        // If d.available is undefined (cold-start empty response), leave button as-is
      })
      .catch(function() {
        // On error, leave button as-is (fail open)
      });
  }

  // Check immediately on load, then every 60 seconds
  checkLibrarianAvailability();
  setInterval(checkLibrarianAvailability, 60000);

  // --- Patron identity form (shown on first open, before any interaction) ---
  // _patronType and _patronDetails are already declared above from stored session state.

  var _PATRON_TYPES = [
    { label: "🎓 Student (Higher Ed)",   value: "Student (Higher Ed)",   prompt: "Please enter your Course & Year (e.g. BSIT 3rd Year):" },
    { label: "📚 Student (Basic Ed)",    value: "Student (Basic Ed)",    prompt: "Please enter your Grade & Section (e.g. Grade 10 - Rizal):" },
    { label: "👩‍🏫 Faculty / Staff",       value: "Faculty / Staff",       prompt: "Please enter your Department (e.g. College of Engineering):" },
    { label: "🏛️ Alumni",               value: "Alumni",                anonymous: true },
    { label: "🙋 Visitor",              value: "Visitor",               anonymous: true },
  ];

  // Lock/unlock helpers — keep input + librarian btn + FAQs disabled until identity is set
  function _lockChat() {
    inp.disabled = true;
    inp.placeholder = "Please identify yourself first…";
    btn.disabled = true;
    libBtn.disabled = true;
    libBtn.style.opacity = "0.45";
  }
  function _unlockChat() {
    inp.disabled = false;
    inp.placeholder = "Ask me about the library...";
    btn.disabled = !inp.value.trim();
    libBtn.disabled = false;
    if (libBtnAvailable) {
      libBtn.style.opacity = "1";
    } else {
      libBtn.style.opacity = "0.6";
    }
  }

  function _onIdentityComplete() {
    // POST patron info to server
    fetch(CHATBOT_API + "/api/patron-info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sid, patron_type: _patronType, patron_details: _patronDetails })
    }).catch(function() {});
    saveState();
    // Show a subtle identity badge so the user knows what info was recorded
    var badge = document.createElement("div");
    badge.id = "lc-identity-badge";
    badge.style.cssText = "align-self:center;font-size:.75rem;color:#666;background:#f0f0ec;" +
      "border:1px solid #ddd;border-radius:20px;padding:4px 12px;margin:4px 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:90%";
    var label = "👤 " + _patronType + (_patronDetails ? " — " + _patronDetails : "");
    badge.textContent = label;
    msgs.appendChild(badge);
    // Reveal the welcome message and FAQs now that identity is set
    var wEl = msgs.querySelector(".lc-w");
    if (wEl) wEl.style.display = "";
    var fqEl = msgs.querySelector(".lc-faqs");
    if (fqEl) fqEl.style.display = "";
    scroll();
    _unlockChat();
    // Re-check availability now so the librarian button reflects the real server state
    checkLibrarianAvailability();
    inp.focus();
  }

  function showPatronTypeStep() {
    // Remove any existing identity form
    var old = document.getElementById("lc-patron-form");
    if (old) old.remove();

    // Bot message asking for type
    var botMsg = document.createElement("div");
    botMsg.className = "lc-m b";
    botMsg.id = "lc-patron-form";
    botMsg.style.cssText = "max-width:90%;white-space:normal";
    botMsg.innerHTML =
      '<div style="margin-bottom:10px;font-size:.9em;line-height:1.5">' +
      'To assist you better, please provide the following details:' +
      '</div>' +
      '<div style="display:flex;flex-direction:column;gap:6px">' +
      _PATRON_TYPES.map(function(t) {
        return '<button class="lc-patron-type-btn" data-value="' + t.value + '" data-prompt="' + (t.prompt || "").replace(/"/g, "&quot;") + '" data-anonymous="' + (t.anonymous ? "true" : "false") + '" ' +
          'style="background:#fff;border:1px solid #D4A017;color:#0E553F;border-radius:14px;' +
          'padding:8px 14px;font-size:.82rem;cursor:pointer;text-align:left;transition:all .15s">' +
          t.label + '</button>';
      }).join("") +
      '</div>';
    msgs.appendChild(botMsg);
    scroll();

    // Attach click handlers
    botMsg.querySelectorAll(".lc-patron-type-btn").forEach(function(b) {
      b.addEventListener("click", function() {
        _patronType = b.getAttribute("data-value");
        var prompt = b.getAttribute("data-prompt");
        var anonymous = b.getAttribute("data-anonymous") === "true";
        // Don't render as a chat bubble — just remove the form and proceed
        if (anonymous) {
          _patronDetails = "";
          var f = document.getElementById("lc-patron-form");
          if (f) f.remove();
          _onIdentityComplete();
        } else {
          showPatronDetailsStep(prompt);
        }
      });
    });
  }

  function showPatronDetailsStep(prompt) {
    var old = document.getElementById("lc-patron-form");
    if (old) old.remove();

    var detailMsg = document.createElement("div");
    detailMsg.className = "lc-m b";
    detailMsg.id = "lc-patron-form";
    detailMsg.style.cssText = "max-width:90%;white-space:normal";
    detailMsg.innerHTML =
      '<div style="margin-bottom:8px;font-size:.9em">' + prompt + '</div>' +
      '<div style="display:flex;gap:6px">' +
      '<input id="lc-patron-detail-input" type="text" placeholder="Type here…" ' +
      'style="flex:1;padding:8px 12px;border:1px solid #ccc;border-radius:14px;font-size:.85rem;outline:none" />' +
      '<button id="lc-patron-detail-btn" ' +
      'style="background:#0E553F;color:#fff;border:none;border-radius:14px;padding:8px 14px;font-size:.82rem;cursor:pointer">' +
      'OK</button>' +
      '</div>';
    msgs.appendChild(detailMsg);
    scroll();

    var detailInput = document.getElementById("lc-patron-detail-input");
    var detailBtn   = document.getElementById("lc-patron-detail-btn");
    detailInput.focus();

    function submitDetails() {
      var val = detailInput.value.trim();
      if (!val) { detailInput.style.borderColor = "#e74c3c"; return; }
      _patronDetails = val;
      // Don't render as a chat bubble — just remove the form and proceed
      var f = document.getElementById("lc-patron-form");
      if (f) f.remove();
      _onIdentityComplete();
    }

    detailBtn.addEventListener("click", submitDetails);
    detailInput.addEventListener("keydown", function(e) {
      if (e.key === "Enter") { e.preventDefault(); submitDetails(); }
    });
  }

  // Show identity form on first open if not yet identified; otherwise unlock immediately
  var _identityDone = !!_patronType;
  if (!_identityDone) {
    _lockChat();
    // Hide welcome message and FAQs until identity is complete
    var _initWel = msgs.querySelector(".lc-w");
    if (_initWel) _initWel.style.display = "none";
    var _initFaq = msgs.querySelector(".lc-faqs");
    if (_initFaq) _initFaq.style.display = "none";
    // If the chat is already open on load, show the form immediately
    if (wasOpen) {
      showPatronTypeStep();
      _identityDone = true; // FAB handler won't re-show it
    }
    // If chat is closed, the FAB click handler will show the form on first open
  }
  // (If identity already set from a previous session, chat is fully unlocked by default)

  libBtn.addEventListener("click", function () {
    if (handoffActive) return; // already in handoff, ignore
    if (!libBtnAvailable) {
      // Outside library hours — fetch hours and show specific availability message
      var w = msgs.querySelector(".lc-w"); if (w) w.remove();
      var fq = msgs.querySelector(".lc-faqs"); if (fq) fq.remove();
      fetch(CHATBOT_API + "/api/librarian-available?t=" + Date.now())
        .then(function(r) { return r.json(); })
        .then(function(d) {
          var hoursInfo = d.reason || "Please check back during library hours.";
          var msg =
            "Hello! Our librarians are currently offline. 🕐\n\n" +
            hoursInfo + "\n\n" +
            "Please note your questions and ask a librarian during active hours. " +
            "In the meantime, I'm LLORA and I'll do my best to answer your questions. 📚";
          addMsg(msg, "b");
        })
        .catch(function() {
          addMsg(AFTER_HOURS_MESSAGE, "b");
        });
      return;
    }
    // Identity already collected upfront — go straight to handoff
    libBtn.disabled = true;
    libBtn.style.opacity = "0.45";
    var w = msgs.querySelector(".lc-w"); if (w) w.remove();
    var fq = msgs.querySelector(".lc-faqs"); if (fq) fq.remove();
    inp.value = "Ask a librarian";
    btn.disabled = false;
    send();
  });

  // --- 5-minute inactivity timer ---
  var INACTIVITY_TIMEOUT = 5 * 60 * 1000; // 5 minutes
  var inactivityTimer = null;

  function resetInactivityTimer() {
    if (inactivityTimer) clearTimeout(inactivityTimer);
    // Don't start the timer during an active handoff — the patron may be waiting for a librarian
    if (handoffActive) return;
    inactivityTimer = setTimeout(function () {
      // Don't expire during handoff
      if (handoffActive) return;
      // Close session on server
      if (sid) {
        var blob = new Blob(
          [JSON.stringify({ message: "", session_id: sid })],
          { type: "application/json" }
        );
        navigator.sendBeacon(CHATBOT_API + "/api/close-session", blob);
      }
      addMsg("Session ended due to inactivity. Starting a new chat…", "b");
      setTimeout(function () { resetToNewChat(); }, 2000);
    }, INACTIVITY_TIMEOUT);
  }

  // Start the timer on first load if there's an active chat
  if (chatHistory.length > 0) resetInactivityTimer();

  // New Chat button
  function resetToNewChat() {
    stopPolling();
    if (inactivityTimer) { clearTimeout(inactivityTimer); inactivityTimer = null; }
    handoffHandler = null;
    lastPollTs = 0;
    ratingShown = false;
    _joinedMsgShown = false;
    returnToBot._done = false;
    chatHistory.length = 0;
    // Clear patron identity so the form shows again for the new session
    _patronType = "";
    _patronDetails = "";
    _identityDone = false;
    sid = (typeof crypto !== "undefined" && crypto.randomUUID)
      ? crypto.randomUUID()
      : "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
          var r = (Math.random() * 16) | 0;
          return (c === "x" ? r : (r & 0x3) | 0x8).toString(16);
        });
    msgs.innerHTML =
      '<div class="lc-w" style="display:none">Hello, I\'m LLORA (Lorma Library Online Research Assistant), your virtual assistant. I\'m here to provide the assistance you need. I\'ll be happy to serve you.</div>' +
      '<div class="lc-faqs" id="lc-faqs-reset" style="display:none"></div>';
    var resetFaqContainer = document.getElementById("lc-faqs-reset");
    if (resetFaqContainer) loadAndRenderFaqs(resetFaqContainer);
    // Lock and show identity form for the new session
    _lockChat();
    showPatronTypeStep();
    _identityDone = true; // mark so FAB re-open doesn't show it again
    // Re-check librarian availability after reset
    checkLibrarianAvailability();
    saveState();
  }

  document.getElementById("lc-new").addEventListener("click", function () {
    // Close the old session on the server
    if (sid) {
      var oldSid = sid;
      fetch(CHATBOT_API + "/api/close-session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "", session_id: oldSid })
      }).catch(function () {
        // Fallback to sendBeacon if fetch fails
        var blob = new Blob(
          [JSON.stringify({ message: "", session_id: oldSid })],
          { type: "application/json" }
        );
        navigator.sendBeacon(CHATBOT_API + "/api/close-session", blob);
      });
    }
    resetToNewChat();
    inp.focus();
  });

  // Send
  function send() {
    var text = inp.value.trim();
    if (!text) return;
    resetInactivityTimer();
    var w = msgs.querySelector(".lc-w"); if (w) w.remove();
    var fq = msgs.querySelector(".lc-faqs"); if (fq) fq.remove();
    addMsg(text, "u");
    inp.value = "";
    // During active handoff, always use the silent path — the backend routes
    // the message to the live chat session regardless of whether the librarian
    // has joined yet (handoffHandler may be null while waiting).
    if (handoffActive) {
      // Get the last message bubble we just added so we can update its status
      var lastBubble = msgs.lastElementChild;
      fetch(CHATBOT_API + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sid })
      }).then(function(r) {
        if (lastBubble && r.ok) {
          var tick = document.createElement("span");
          tick.style.cssText = "font-size:.7rem;opacity:.6;margin-left:6px";
          tick.textContent = "✓";
          lastBubble.appendChild(tick);
        }
      }).catch(function() {
        if (lastBubble) {
          var err = document.createElement("span");
          err.style.cssText = "font-size:.7rem;color:#e74c3c;margin-left:6px";
          err.textContent = "✗ not sent";
          lastBubble.appendChild(err);
        }
      });
      inp.disabled = false; inp.focus(); btn.disabled = false;
      return;
    }
    btn.disabled = true; inp.disabled = true;
    var lower = text.toLowerCase();
    var isSearch = /\b(find|search|look|book|books|author|title|catalog|isbn)\b/.test(lower);
    showTyping(isSearch ? "Searching…" : "Thinking…");
    var chatAbort = new AbortController();
    var chatTimeout = setTimeout(function() { chatAbort.abort(); }, 25000);
    fetch(CHATBOT_API + "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sid }),
      signal: chatAbort.signal
    })
    .then(function (r) {
      clearTimeout(chatTimeout);
      if (!r.ok) return r.json().then(function (d) { throw new Error(d.error || "Request failed"); });
      return r.json();
    })
    .then(function (d) {
      // If server says to do client-side search, fetch Koha RSS directly
      if (d.client_search) {
        var kohaBase = "";
        // Detect Koha OPAC origin — if we're on the OPAC, use same origin
        if (window.location.hostname.indexOf("lorma") !== -1 || document.querySelector("#opac-main-search")) {
          kohaBase = window.location.origin;
        } else {
          kohaBase = "https://library.lorma.edu";
        }
        var rssUrl = kohaBase + "/cgi-bin/koha/opac-search.pl?q=" + encodeURIComponent("ti:" + d.client_search + " OR au:" + d.client_search + " OR " + d.client_search) + "&format=rss";
        fetch(rssUrl)
          .then(function(r) { return r.text(); })
          .then(function(xml) {
            var parser = new DOMParser();
            var doc = parser.parseFromString(xml, "text/xml");
            var items = doc.querySelectorAll("item");
            var results = [];
            items.forEach(function(item, idx) {
              if (idx >= 20) return;
              var title = item.querySelector("title");
              var link = item.querySelector("link");
              var creator = item.getElementsByTagNameNS("http://purl.org/dc/elements/1.1/", "creator");
              var author = (creator.length > 0 && creator[0].textContent.trim()) ? creator[0].textContent.trim() : "";
              // If no dc:creator, extract from description "By Author.<br"
              if (!author) {
                var desc = item.querySelector("description");
                if (desc && desc.textContent) {
                  var byMatch = desc.textContent.match(/By\s+(.+?)\.\s*<br/);
                  if (byMatch) author = byMatch[1].trim();
                }
              }
              results.push({
                title: title ? title.textContent.trim() : "Unknown",
                author: author || "Unknown Author",
                url: link ? kohaBase + link.textContent.trim() : ""
              });
            });
            // Send results to backend for formatting
            return fetch(CHATBOT_API + "/api/format-results", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ results: results, session_id: sid, message: d.client_search })
            });
          })
          .then(function(r) { return r.json(); })
          .then(function(d2) { hideTyping(); if (d2.reply) addMsg(d2.reply, "b", d2.timestamp); })
          .catch(function() {
            hideTyping();
            addMsg("Hmm, I couldn't search the catalog right now. Try searching directly on the library website! 🔍", "e");
          });
        return;
      }
      hideTyping(); if (d.reply || d.image_url || d.pdf_url) addMsg(d.reply || "", "b", d.timestamp, d.image_url || null, d.pdf_url || null);
    })
    .catch(function (err) {
      hideTyping();
      // Try to give a helpful static answer for common library info questions
      var q = text.toLowerCase();
      if (q.match(/hour|open|close|schedule/)) {
        addMsg("The CHS Library is open Monday to Friday from 7:00 AM to 7:00 PM, and on Saturdays from 8:30 AM to 4:30 PM. The CLI Library is open Monday to Friday from 7:30 AM to 5:00 PM. The High School Library and Preschool/Grade School Library are open Monday to Friday from 8:30 AM to 4:30 PM. All branches are closed on Sundays. 📚", "b");
      } else if (q.match(/email|contact/)) {
        addMsg("You can reach us at chslibrary@lorma.edu (CHS) or clilibrary@lorma.edu (CLI). 📧", "b");
      } else {
        addMsg("I'm taking a bit longer than usual to respond 😅 Please send your message again — I'll be ready!", "e");
      }
    })
    .finally(function () {
      inp.disabled = false; inp.focus(); btn.disabled = !inp.value.trim();
    });
  }

  // --- Librarian handoff polling + Ably real-time ---
  var handoffActive = false;
  var handoffHandler = null;
  var lastPollTs = 0;
  var pollTimer = null;
  var _joinedMsgShown = false;
  var _returnToBotTimer = null;
  var _seenMsgKeys = {}; // tracks keys of messages already rendered by the poll
  var _ablyClient = null;
  var _ablyChannel = null;
  var _ablyLiveChatId = null;

  function _initAbly(liveChatId, onMessage, onStatus) {
    if (_ablyClient && _ablyLiveChatId === liveChatId) return; // already subscribed
    _ablyLiveChatId = liveChatId;
    // Load Ably SDK from CDN if not already loaded
    function connectAbly(key) {
      try {
        if (typeof Ably === "undefined") return; // SDK not loaded yet
        if (_ablyClient) { try { _ablyClient.close(); } catch(e) {} }
        _ablyClient = new Ably.Realtime({ key: key, recover: function(_, cb) { cb(true); } });
        _ablyChannel = _ablyClient.channels.get("live-chat:" + liveChatId);
        _ablyChannel.subscribe("message", function(msg) {
          if (msg.data) onMessage(msg.data);
        });
        _ablyChannel.subscribe("status", function(msg) {
          if (msg.data) onStatus(msg.data);
        });
      } catch(e) {}
    }
    fetch(CHATBOT_API + "/api/ably-token")
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (!d.key) return;
        if (typeof Ably !== "undefined") {
          connectAbly(d.key);
        } else {
          // Load SDK then connect
          var s = document.createElement("script");
          s.src = "https://cdn.ably.com/lib/ably.min-2.js";
          s.onload = function() { connectAbly(d.key); };
          document.head.appendChild(s);
        }
      })
      .catch(function() {});
  }

  function _stopAbly() {
    try {
      if (_ablyChannel) { _ablyChannel.unsubscribe(); _ablyChannel = null; }
      if (_ablyClient) { _ablyClient.close(); _ablyClient = null; }
    } catch(e) {}
    _ablyLiveChatId = null;
  }

  function startPolling() {
    if (pollTimer) return;
    handoffActive = true;
    libBtn.style.opacity = "0.5";
    libBtn.style.cursor = "default";
    inp.disabled = true;
    inp.placeholder = "Waiting for a librarian…";
    btn.disabled = true;
    showCancelButton();
    // Fallback poll every 4s (Ably handles real-time; poll catches missed events)
    pollTimer = setInterval(pollForMessages, 4000);
  }

  function _startAblyForLiveChat(liveChatId) {
    _initAbly(liveChatId,
      function onMessage(data) {
        // New message from Ably — same dedup logic as poll
        var key = data.id != null ? ("id:" + data.id) : (data.timestamp + "|" + data.content);
        if (_seenMsgKeys[key]) return;
        if (data.role === "librarian") {
          addMsgRaw("👩‍💼 Librarian: " + data.content, "b", data.timestamp);
        } else if (data.role === "assistant") {
          if (!data.content || data.content.indexOf("LLORA") !== -1 || data.content.indexOf("ended the chat") !== -1 || data.content.indexOf("notified a librarian") !== -1) return;
          addMsgRaw(data.content, "b", data.timestamp);
        }
        _seenMsgKeys[key] = true;
        if (data.timestamp > lastPollTs) lastPollTs = data.timestamp;
      },
      function onStatus(data) {
        if (data.status === "active" && data.staff_username && !handoffHandler) {
          handoffHandler = data.staff_username;
          removeCancelButton();
          inp.disabled = false;
          inp.placeholder = "Type your message…";
          btn.disabled = false;
          if (!_joinedMsgShown) {
            _joinedMsgShown = true;
            _origAddMsg("A librarian has joined the chat! 👋", "b");
          }
        } else if (data.status === "ended" && handoffActive && handoffHandler) {
          stopPolling(true);
          _stopAbly();
          showHandoffRating();
        }
      }
    );
  }

  function stopPolling(keepInputDisabled) {
    handoffActive = false;
    handoffHandler = null;
    lastPollTs = 0;
    // Don't reset _joinedMsgShown here — a queued poll tick firing after stopPolling
    // would re-show the "joined" message if we clear the flag now.
    _seenMsgKeys = {};
    if (libBtnAvailable) {
      libBtn.style.opacity = "1";
      libBtn.style.cursor = "pointer";
      libBtn.disabled = false;
    }
    if (!keepInputDisabled) {
      inp.disabled = false;
      inp.placeholder = "Type your message…";
      btn.disabled = false;
    }
    removeCancelButton();
    if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    _stopAbly();
    resetInactivityTimer();
    checkLibrarianAvailability();
  }

  function showCancelButton() {
    removeCancelButton();
    var cancelDiv = document.createElement("div");
    cancelDiv.id = "lc-cancel-handoff";
    cancelDiv.className = "lc-m b";
    cancelDiv.style.cssText = "text-align:center;max-width:90%;padding:10px 14px";
    cancelDiv.innerHTML =
      '<button style="background:none;border:1px solid #c0392b;color:#c0392b;border-radius:14px;' +
      'padding:6px 16px;font-size:.82rem;cursor:pointer;transition:all .15s" ' +
      'aria-label="Cancel librarian request">Cancel request</button>';
    cancelDiv.querySelector("button").addEventListener("click", cancelHandoff);
    msgs.appendChild(cancelDiv);
    scroll();
  }

  function removeCancelButton() {
    var el = document.getElementById("lc-cancel-handoff");
    if (el) el.remove();
  }

  function cancelHandoff() {
    fetch(CHATBOT_API + "/api/cancel-handoff", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "", session_id: sid })
    })
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (d.status === "ok") {
          stopPolling();
          _origAddMsg("Librarian request cancelled. 👋 I'm LLORA, your AI assistant — what can I help you with?", "b");
        } else if (d.error) {
          removeCancelButton(); // Staff already claimed — keep polling
        }
      })
      .catch(function() {});
  }

  function pollForMessages() {
    fetch(CHATBOT_API + "/api/poll/" + encodeURIComponent(sid) + "?since=" + lastPollTs)
      .then(function(r) { return r.json(); })
      .then(function(d) {
        // Subscribe to Ably channel as soon as we know the live_chat_id
        if (d.live_chat_id && d.live_chat_id !== _ablyLiveChatId) {
          _startAblyForLiveChat(d.live_chat_id);
        }

        // Librarian joined — only show if we're still in an active handoff
        if (d.handled_by && d.handled_by !== handoffHandler && handoffActive) {
          handoffHandler = d.handled_by;
          removeCancelButton();
          inp.disabled = false;
          inp.placeholder = "Type your message…";
          btn.disabled = false;
          if (!_joinedMsgShown) {
            _joinedMsgShown = true;
            _origAddMsg("A librarian has joined the chat! 👋", "b");
          }
        }

        // New messages — use id-based deduplication to avoid missing or duplicating messages
        if (d.messages && d.messages.length > 0) {
          d.messages.forEach(function(m) {
            // Use id-based deduplication when available, fall back to timestamp|content
            var key = m.id != null ? ("id:" + m.id) : (m.timestamp + "|" + m.content);
            if (_seenMsgKeys[key]) return;
            if (m.role === "librarian") {
              // Use addMsgRaw (no chatHistory save) — poll always re-fetches from DB on reload
              addMsgRaw("👩‍💼 Librarian: " + m.content, "b", m.timestamp);
            } else if (m.role === "assistant") {
              if (!m.content || m.content.indexOf("LLORA") !== -1 || m.content.indexOf("ended the chat") !== -1 || m.content.indexOf("notified a librarian") !== -1) return;
              _origAddMsg(m.content, "b", m.timestamp);
            }
            _seenMsgKeys[key] = true;
            if (m.timestamp > lastPollTs) {
              lastPollTs = m.timestamp;
            }
          });
        }

        // Chat ended — use live_chat_status as the definitive signal
        // This is immune to cold-start false negatives because it checks
        // the actual live_chat_sessions.status column, not the handoff flag
        if (d.live_chat_status === "ended" && handoffActive && handoffHandler) {
          stopPolling(true);
          showHandoffRating();
        } else if (!d.handoff_active && !d.live_chat_status && handoffActive && !handoffHandler) {
          // No live chat at all and no librarian joined — cancelled or expired
          stopPolling();
        }

        // Librarian typing indicator
        if (handoffActive && handoffHandler) {
          fetch(CHATBOT_API + "/api/typing/" + encodeURIComponent(sid))
            .then(function(r) { return r.json(); })
            .then(function(t) {
              var el = document.getElementById("lc-lib-typing");
              if (t.librarian_typing) {
                if (!el) {
                  el = document.createElement("div");
                  el.id = "lc-lib-typing";
                  el.className = "lc-t";
                  el.textContent = "Librarian is typing…";
                  msgs.appendChild(el);
                  scroll();
                }
              } else if (el) { el.remove(); }
            }).catch(function(){});
        }
      })
      .catch(function() {});
  }

  var ratingShown = false;
  function showHandoffRating() {
    if (ratingShown) return;
    ratingShown = true;
    _origAddMsg("The librarian has ended the chat. 👋", "b");
    var rateDiv = document.createElement("div");
    rateDiv.className = "lc-m b";
    rateDiv.style.cssText = "text-align:center;max-width:95%;padding:14px 18px;white-space:normal";
    rateDiv.innerHTML =
      '<div style="margin-bottom:10px;font-size:0.92em;color:#333;font-weight:600">How satisfied were you with the librarian\'s assistance?</div>' +
      '<div class="lc-handoff-rate" style="flex-direction:column;gap:6px;align-items:stretch">' +
      '<button class="lc-rate-btn" data-rating="4" aria-label="Very Satisfied" style="text-align:left">😄 4 — Very Satisfied</button>' +
      '<button class="lc-rate-btn" data-rating="3" aria-label="Satisfied" style="text-align:left">&#128077; 3 — Satisfied</button>' +
      '<button class="lc-rate-btn" data-rating="2" aria-label="Moderately Satisfied" style="text-align:left">&#128076; 2 — Moderately Satisfied</button>' +
      '<button class="lc-rate-btn" data-rating="1" aria-label="Not Satisfied" style="text-align:left">😞 1 — Not Satisfied</button>' +
      '</div>';
    msgs.appendChild(rateDiv);
    scroll();
    rateDiv.querySelectorAll(".lc-rate-btn").forEach(function(rBtn) {
      rBtn.addEventListener("click", function() {
        var rating = parseInt(rBtn.getAttribute("data-rating"));
        var labels = { 4: "Very Satisfied 😄", 3: "Satisfied 🙂", 2: "Moderately Satisfied 😐", 1: "Not Satisfied 😞" };
        rateDiv.innerHTML = '<div style="color:#555;font-size:0.88rem">Thanks for your feedback! You rated: <strong>' + (labels[rating] || rating) + '</strong></div>';
        fetch(CHATBOT_API + "/api/rate-handoff", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sid, rating: rating })
        }).catch(function() {});
        returnToBot();
      });
    });
    // Auto-return after 10s if patron skips rating
    if (_returnToBotTimer) clearTimeout(_returnToBotTimer);
    _returnToBotTimer = setTimeout(returnToBot, 10000);
  }

  function returnToBot() {
    if (returnToBot._done) return;
    returnToBot._done = true;
    if (_returnToBotTimer) { clearTimeout(_returnToBotTimer); _returnToBotTimer = null; }
    ratingShown = false;
    _origAddMsg("👩‍💼 LLORA (AI Assistant) is back! 🤖 What else can I help you with?", "b");
    inp.disabled = false;
    inp.placeholder = "Ask me about the library...";
    btn.disabled = !inp.value.trim();
    inp.focus();
    scroll();
  }
  returnToBot._done = false;

  // Detect handoff activation from bot responses
  var _origAddMsg = addMsg;
  addMsg = function(t, c, ts, imgUrl, pdfUrl) {
    _origAddMsg(t, c, ts, imgUrl || null, pdfUrl || null);
    if (c === "b" && t && t.indexOf("notified a librarian") !== -1) {
      handoffHandler = null;
      returnToBot._done = false;
      ratingShown = false;
      // Start from 0 so we don't miss librarian messages sent in the first
      // poll interval. The _seenMsgKeys dedup prevents double-rendering.
      lastPollTs = 0;
      startPolling();
    }
  };

  // On load, resume polling if handoff is still active
  (function resumeHandoffIfActive() {
    if (!sid) return;
    fetch(CHATBOT_API + "/api/poll/" + encodeURIComponent(sid) + "?since=0")
      .then(function(r) { return r.json(); })
      .then(function(d) {
        if (d.handoff_active) {
          lastPollTs = 0;
          if (d.handled_by) {
            handoffHandler = d.handled_by;
            _joinedMsgShown = true;
          }

          // Re-render the full conversation in correct timestamp order.
          // Merge chatHistory entries (patron/system) with librarian messages from DB.
          if (d.messages && d.messages.length > 0) {
            // Build a combined list sorted by timestamp
            var combined = [];
            chatHistory.forEach(function(m) {
              if (m.cls === "b" && m.text && m.text.indexOf("👩‍💼 Librarian:") === 0) return;
              combined.push({ ts: m.ts || 0, render: function(entry) {
                addMsgRaw(entry.text, entry.cls, entry.ts, entry.imgUrl || null, entry.pdfUrl || null);
              }, text: m.text, cls: m.cls, imgUrl: m.imgUrl, pdfUrl: m.pdfUrl, isHistory: true });
            });
            d.messages.forEach(function(m) {
              var key = m.id != null ? ("id:" + m.id) : (m.timestamp + "|" + m.content);
              _seenMsgKeys[key] = true;
              if (m.timestamp > lastPollTs) lastPollTs = m.timestamp;
              if (m.role === "librarian") {
                combined.push({ ts: m.timestamp || 0, content: m.content, isLibrarian: true });
              }
              // skip user — already in chatHistory
              // skip assistant — already in chatHistory (system messages like "notified a librarian")
            });
            combined.sort(function(a, b) { return (a.ts || 0) - (b.ts || 0); });

            msgs.innerHTML = "";
            combined.forEach(function(entry) {
              if (entry.isLibrarian) {
                addMsgRaw("👩‍💼 Librarian: " + entry.content, "b", entry.ts);
              } else {
                addMsgRaw(entry.text, entry.cls, entry.ts, entry.imgUrl || null, entry.pdfUrl || null);
              }
            });
            scroll();
          }

          startPolling();
          if (d.handled_by) {
            inp.disabled = false;
            inp.placeholder = "Type your message…";
            btn.disabled = false;
            removeCancelButton();
          }
        }
        // If not active, do nothing — no spurious end-of-chat UI
      })
      .catch(function() {});
  })();

  // Notify server when patron closes/navigates away so session is marked expired
  window.addEventListener("beforeunload", function () {
    stopPolling();
    if (sid) {
      var blob = new Blob(
        [JSON.stringify({ message: "", session_id: sid })],
        { type: "application/json" }
      );
      navigator.sendBeacon(CHATBOT_API + "/api/close-session", blob);
    }
  });
})();
