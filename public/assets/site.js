// Shared by every page. Fill these in when ready. Leave empty to show the "opens soon" state.
var CONFIG = {
  whatsappNumber: "", // international format, digits only, e.g. "263771234567"
  bookingUrl: ""      // e.g. your Cal.com or Calendly free-trial link
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

  var year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
