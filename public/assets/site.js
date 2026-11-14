// Shared by every page. Fill these in when ready. Leave empty to show the "opens soon" state.
var CONFIG = {
  whatsappNumber: "", // international format, digits only, e.g. "263771234567"
  bookingUrl: "",     // e.g. your Cal.com or Calendly free-trial link

  // Shown on the home page under "Bring a friend". Leave empty to hide it.
  // e.g. "Refer a family and you both get one free lesson when they join."
  referralOffer: "",

  // Real parent reviews for the home page. Leave the list empty to hide the section.
  // Only add words a parent really said, and ask them first. Copy this line for each one:
  //   { quote: "What the parent said.", name: "First name", place: "City, Country" },
  reviews: []
};

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

  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
