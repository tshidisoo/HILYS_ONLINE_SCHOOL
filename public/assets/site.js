// Shared by every page. Fill these in when ready. Leave empty to show the "opens soon" state.
var CONFIG = {
  whatsappNumber: "", // international format, digits only, e.g. "263771234567"
  bookingUrl: "",     // e.g. your Cal.com or Calendly free-trial link

  // The HILYS management system's address. Enquiry forms send to it, and each one arrives as a lead.
  // e.g. "https://api.hilys.com". Left empty, the site uses the local system on this computer while
  // testing, and falls back to WhatsApp when it is live.
  apiUrl: "",

  // Shown on the home page under "Bring a friend". Leave empty to hide it.
  // e.g. "Refer a family and you both get one free lesson when they join."
  referralOffer: "",

  // Real parent reviews for the home page. Leave the list empty to hide the section.
  // Only add words a parent really said, and ask them first. Copy this line for each one:
  //   { quote: "What the parent said.", name: "First name", place: "City, Country" },
  reviews: []
};

// Where enquiries go: the setting above, or the local management system while testing on this computer.
CONFIG.api = CONFIG.apiUrl || (/^(localhost|127\.0\.0\.1)$/.test(location.hostname) ? "http://127.0.0.1:8000" : "");

(function () {
  var defaultText = "Hello HILYS, I'd like to book a free trial isiNdebele lesson for my child.";
  var missing = false;

  // A button can carry its own message: data-whatsapp="Hello HILYS, ..."
  document.querySelectorAll("[data-whatsapp]").forEach(function (a) {
    if (CONFIG.whatsappNumber) {
      var text = a.getAttribute("data-whatsapp") || defaultText;
      a.href = "https://wa.me/" + CONFIG.whatsappNumber + "?text=" + encodeURIComponent(text);
      a.target = "_blank"; a.rel = "noopener";
    } else if (a.closest(".trial")) {
      a.setAttribute("aria-disabled", "true"); missing = true;
    }
  });

  document.querySelectorAll("[data-booking]").forEach(function (a) {
    if (!CONFIG.bookingUrl && CONFIG.api) {
      a.setAttribute("data-enquire", a.getAttribute("data-enquire") || "live");
      return;
    }
    if (CONFIG.bookingUrl) {
      a.href = CONFIG.bookingUrl; a.target = "_blank"; a.rel = "noopener";
    } else {
      a.setAttribute("aria-disabled", "true"); missing = true;
    }
  });

  document.querySelectorAll("[aria-disabled='true']").forEach(function (a) {
    a.addEventListener("click", function (e) { e.preventDefault(); });
  });

  var note = document.querySelector("[data-contact-note]");
  if (missing && note) note.hidden = false;

  // Home page: parent reviews and the referral offer. The band stays hidden while both are empty.
  var band = document.querySelector("[data-reviews-band]");
  if (band && (CONFIG.reviews.length || CONFIG.referralOffer)) {
    band.hidden = false;
    var list = band.querySelector("[data-reviews]");
    CONFIG.reviews.forEach(function (r) {
      var card = document.createElement("figure"), quote = document.createElement("blockquote"),
          who = document.createElement("figcaption"), name = document.createElement("strong");
      card.className = "review";
      quote.textContent = r.quote;
      name.textContent = r.name;
      who.appendChild(name);
      if (r.place) who.appendChild(document.createTextNode(" · " + r.place));
      card.appendChild(quote); card.appendChild(who); list.appendChild(card);
    });
    if (!CONFIG.reviews.length) {
      band.querySelector("[data-reviews-head]").hidden = true; list.hidden = true;
    }
    if (CONFIG.referralOffer) {
      band.querySelector("[data-refer]").hidden = false;
      band.querySelector("[data-refer-text]").textContent = CONFIG.referralOffer;
    }
  }

  // Enquiry form: any button with data-enquire="live|video|plus" opens it when the management system is reachable.
  if (CONFIG.api) {
    document.querySelectorAll("[data-enquire]").forEach(function (a) {
      a.removeAttribute("aria-disabled");
      a.removeAttribute("target");
      a.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopImmediatePropagation();
        openEnquiry(a.getAttribute("data-enquire"), a.getAttribute("data-level") || "");
      }, true);
    });
    if (missing && note && !document.querySelector("[data-whatsapp][aria-disabled='true']")) note.hidden = true;
  }

  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();

// The enquiry form. Built once, reused by every button. Labels and messages are plain words.
function openEnquiry(interest, level) {
  var titles = { live: "Book a free trial lesson", video: "Join the video course waiting list", plus: "Join the HILYS Plus waiting list" };
  var dlg = document.getElementById("enquiry");
  if (!dlg) {
    dlg = document.createElement("dialog");
    dlg.id = "enquiry";
    dlg.className = "enquiry";
    dlg.setAttribute("aria-labelledby", "enquiry-title");
    dlg.innerHTML =
      '<form method="dialog" novalidate>' +
      '<div class="enq-head"><h2 id="enquiry-title"></h2><button type="button" class="enq-close" aria-label="Close">×</button></div>' +
      '<p class="enq-lede">Tell us a little about your child. We reply within one working day.</p>' +
      '<div class="enq-grid">' +
      '<label>Your name<input name="parent_name" autocomplete="name" required></label>' +
      '<label>Your email<input name="email" type="email" autocomplete="email"></label>' +
      '<label>Your WhatsApp number<input name="phone" type="tel" autocomplete="tel" placeholder="+44 7700 900123"></label>' +
      '<label>Where you live<select name="country"><option value="GB">United Kingdom</option><option value="ZA">South Africa</option><option value="AU">Australia</option><option value="US">United States</option><option value="CA">Canada</option><option value="IE">Ireland</option><option value="NZ">New Zealand</option><option value="BW">Botswana</option><option value="ZW">Zimbabwe</option><option value="">Somewhere else</option></select></label>' +
      '<label>Your child\'s first name<input name="child_name"></label>' +
      '<label>Your child\'s age<input name="child_age" type="number" min="3" max="18" inputmode="numeric"></label>' +
      '<label class="enq-wide">Anything we should know? (optional)<textarea name="message" rows="3"></textarea></label>' +
      '<label class="enq-trap" aria-hidden="true">Leave this empty<input name="website" tabindex="-1" autocomplete="off"></label>' +
      '</div>' +
      '<p class="enq-error" role="alert" hidden></p>' +
      '<div class="enq-actions"><button type="submit" class="btn btn-primary">Send</button><span class="enq-small">We use your details only to reply and arrange lessons.</span></div>' +
      '</form>' +
      '<div class="enq-done" hidden><h2>Ngiyabonga!</h2><p>Thank you. We\'ll reply within one working day, usually on WhatsApp.</p><button type="button" class="btn btn-ghost enq-close">Close</button></div>';
    document.body.appendChild(dlg);
    dlg.querySelectorAll(".enq-close").forEach(function (b) { b.addEventListener("click", function () { dlg.close(); }); });
    dlg.addEventListener("click", function (e) { if (e.target === dlg) dlg.close(); });
    dlg.querySelector("form").addEventListener("submit", function (e) {
      e.preventDefault();
      var f = e.target, err = dlg.querySelector(".enq-error"), btn = f.querySelector("button[type=submit]");
      var data = {};
      new FormData(f).forEach(function (v, k) { data[k] = String(v).trim(); });
      if (!data.parent_name) { err.textContent = "Please tell us your name."; err.hidden = false; f.parent_name.focus(); return; }
      if (!data.email && !data.phone) { err.textContent = "Please give an email or a WhatsApp number so we can reply."; err.hidden = false; f.email.focus(); return; }
      data.child_age = data.child_age ? Number(data.child_age) : null;
      data.interest = dlg.dataset.interest;
      data.suggested_level = dlg.dataset.level || "";
      data.source = dlg.dataset.level ? "Level check" : "Website";
      try { data.time_zone = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (x) { data.time_zone = ""; }
      err.hidden = true; btn.disabled = true; btn.textContent = "Sending…";
      fetch(CONFIG.api + "/api/public/enquiry/", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
        .then(function (r) {
          if (r.status === 429) throw new Error("Too many tries. Please wait a little, or message us on WhatsApp.");
          if (!r.ok) throw new Error("Please check the form and try again.");
          f.hidden = true; dlg.querySelector(".enq-done").hidden = false; f.reset();
        })
        .catch(function (x) {
          err.textContent = x.message && x.message.indexOf("Failed") !== 0 ? x.message : "We could not send this. Check your internet, or message us on WhatsApp.";
          err.hidden = false;
        })
        .then(function () { btn.disabled = false; btn.textContent = "Send"; });
    });
  }
  dlg.dataset.interest = interest || "live";
  dlg.dataset.level = level || "";
  dlg.querySelector("#enquiry-title").textContent = titles[interest] || titles.live;
  dlg.querySelector("form").hidden = false;
  dlg.querySelector(".enq-done").hidden = true;
  dlg.querySelector(".enq-error").hidden = true;
  dlg.showModal();
  dlg.querySelector("input[name=parent_name]").focus();
}

