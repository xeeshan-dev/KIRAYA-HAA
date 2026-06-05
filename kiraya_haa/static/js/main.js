document.addEventListener("click", (event) => {
  if (event.target.matches("[data-dismiss]")) {
    event.target.closest("[data-dismissible]").remove();
  }

  const thumb = event.target.closest(".photo-thumb");
  if (thumb) {
    const main = document.querySelector("#main-photo");
    if (main) {
      main.src = thumb.dataset.photoSrc;
    }
  }
});

document.addEventListener("change", (event) => {
  const input = event.target;
  if (!input.matches("[data-photo-preview]")) {
    return;
  }

  const target = document.getElementById(input.getAttribute("data-photo-preview"));
  if (!target) {
    return;
  }
  target.innerHTML = "";

  Array.from(input.files || []).slice(0, 5).forEach((file) => {
    const image = document.createElement("img");
    image.className = "h-24 w-full rounded-md object-cover";
    image.alt = "";
    image.src = URL.createObjectURL(file);
    target.appendChild(image);
  });
});
