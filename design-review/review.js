const template = document.querySelector("#public-site-template");
const publicScreens = document.querySelectorAll(".public-desktop, .public-mobile");

for (const screen of publicScreens) {
  screen.append(template.content.cloneNode(true));
}

const params = new URLSearchParams(window.location.search);
const captureMode = params.get("capture") === "1";
const validScreens = new Set(
  [...document.querySelectorAll("[data-screen]")].map((screen) => screen.dataset.screen),
);

function selectScreen(name, updateUrl = true) {
  const targetName = validScreens.has(name) ? name : "public-desktop";

  for (const screen of document.querySelectorAll("[data-screen]")) {
    screen.classList.toggle("is-active", screen.dataset.screen === targetName);
  }

  for (const button of document.querySelectorAll("[data-target]")) {
    button.classList.toggle("is-active", button.dataset.target === targetName);
    button.setAttribute("aria-pressed", String(button.dataset.target === targetName));
  }

  if (updateUrl) {
    const next = new URL(window.location.href);
    next.searchParams.set("screen", targetName);
    window.history.replaceState({}, "", next);
  }

  window.scrollTo({ top: 0, behavior: "instant" });
  document.title = `朗泰 LungTic · ${targetName}`;
}

if (captureMode) {
  document.body.classList.add("capture-mode");
  for (const element of document.querySelectorAll("[data-review-only]")) {
    element.hidden = true;
  }
}

for (const button of document.querySelectorAll("[data-target]")) {
  button.addEventListener("click", () => selectScreen(button.dataset.target));
}

for (const anchor of document.querySelectorAll('a[href="#"]')) {
  anchor.addEventListener("click", (event) => event.preventDefault());
}

selectScreen(params.get("screen") || "public-desktop", false);
