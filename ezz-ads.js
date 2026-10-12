/* © 2026 Ezzcoins. All rights reserved. Copying or reuse of this code is not permitted. */
// Google AdSense set-up shared by every page.
// SLOT is the data-ad-slot number of the "Ezzcoins responsive" display ad unit in AdSense.
// While it is empty, no ad boxes appear anywhere (Auto ads, if turned on in AdSense, still work).
(function () {
  var CLIENT = "ca-pub-5351346431839799";
  var SLOT = "";
  // index.html reads this for the side rails on very wide screens.
  window.EZZ_ADS = { client: CLIENT, slotLeft: SLOT, slotRight: SLOT, slotInline: SLOT };
  if (!SLOT) return;

  var css = ".ezz-ad{display:block;box-sizing:border-box;width:100%;margin:22px auto;max-width:100%;min-height:100px;overflow:hidden;text-align:center}" +
    ".ezz-ad[hidden]{display:none}" +
    ".ezz-ad-label{font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;opacity:.55;margin-bottom:4px}" +
    ".ezz-ad:has(ins[data-ad-status=\"unfilled\"]){display:none}";

  function loadScript() {
    if (document.querySelector('script[src*="adsbygoogle.js"]')) return;
    var s = document.createElement("script");
    s.async = true;
    s.crossOrigin = "anonymous";
    s.src = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=" + encodeURIComponent(CLIENT);
    document.head.appendChild(s);
  }

  // A responsive ad needs a visible box with a real width, so each box is filled
  // only once it scrolls into view (boxes inside hidden tabs wait until the tab opens).
  function fill(box) {
    if (box.dataset.filled || !box.offsetWidth) return false;
    box.dataset.filled = "1";
    box.innerHTML = '<div class="ezz-ad-label">Advertisement</div><ins class="adsbygoogle" style="display:block" data-ad-client="' +
      CLIENT + '" data-ad-slot="' + SLOT + '" data-ad-format="auto" data-full-width-responsive="true"></ins>';
    window.adsbygoogle = window.adsbygoogle || [];
    try { window.adsbygoogle.push({}); } catch (e) { /* ad blockers or a not-yet-approved site */ }
    // Blocked or never filled: hide the empty box instead of leaving a gap.
    setTimeout(function () {
      var ins = box.querySelector("ins");
      if (!ins || (!ins.getAttribute("data-ad-status") && !ins.offsetHeight)) box.style.display = "none";
    }, 8000);
    return true;
  }

  function start() {
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);
    loadScript();
    var boxes = Array.prototype.slice.call(document.querySelectorAll(".ezz-ad"));
    if (!boxes.length) return;
    boxes.forEach(function (b) { b.hidden = false; });
    if (!("IntersectionObserver" in window)) { boxes.forEach(fill); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting && fill(en.target)) io.unobserve(en.target); });
    }, { rootMargin: "200px 0px" });
    boxes.forEach(function (b) { io.observe(b); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
