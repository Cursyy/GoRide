(function () {
  const themeToggleButton = document.getElementById("theme-toggle");
  const themeIcon = document.getElementById("theme-icon");
  const accessibilityToggle = document.getElementById("accessibility-toggle");
  const accessibilityIcon = document.getElementById("accessibility-icon");
  if (!themeToggleButton || !themeIcon) {
    console.warn("Theme toggle button or icon not found.");
  }

  const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");
  function setTheme(isDark) {
    const rootElement = document.documentElement;
    if (isDark) {
      rootElement.classList.add("dark-mode");
      if (themeIcon) {
        themeIcon.classList.remove("fa-sun");
        themeIcon.classList.add("fa-moon");
      }
      localStorage.setItem("theme", "dark");
      if (themeToggleButton)
        themeToggleButton.setAttribute("title", "Switch to light theme");
    } else {
      rootElement.classList.remove("dark-mode");
      if (themeIcon) {
        themeIcon.classList.remove("fa-moon");
        themeIcon.classList.add("fa-sun");
      }
      localStorage.setItem("theme", "light");
      if (themeToggleButton)
        themeToggleButton.setAttribute("title", "Switch to dark theme");
    }
    updateThemedImages(isDark);
  }

  if (document.documentElement.classList.contains("dark-mode")) {
    if (themeIcon) {
      themeIcon.classList.remove("fa-sun");
      themeIcon.classList.add("fa-moon");
    }
    if (themeToggleButton)
      themeToggleButton.setAttribute("title", "Switch to light theme");
  } else {
    if (themeIcon) {
      themeIcon.classList.remove("fa-moon");
      themeIcon.classList.add("fa-sun");
    }
    if (themeToggleButton)
      themeToggleButton.setAttribute("title", "Switch to dark theme");
  }

  if (themeToggleButton) {
    themeToggleButton.addEventListener("click", () => {
      setTheme(!document.documentElement.classList.contains("dark-mode"));
    });
  }

  prefersDarkScheme.addEventListener("change", (e) => {
    if (!localStorage.getItem("theme")) {
      setTheme(e.matches);
    }
  });

  if (accessibilityToggle) {
    const savedAccessibility = localStorage.getItem("accessibility") || "off";
    document.documentElement.setAttribute(
      "data-accessibility",
      savedAccessibility,
    );
    if (savedAccessibility === "on") {
      if (accessibilityIcon) {
        accessibilityIcon.classList.remove("fa-universal-access");
        accessibilityIcon.classList.add("fa-eye-slash");
      }
      accessibilityToggle.setAttribute("title", "Disable Accessibility Mode");
    } else {
      if (accessibilityIcon) {
        accessibilityIcon.classList.remove("fa-eye-slash");
        accessibilityIcon.classList.add("fa-universal-access");
      }
      accessibilityToggle.setAttribute("title", "Enable Accessibility Mode");
    }

    accessibilityToggle.addEventListener("click", () => {
      const isAccessibilityOn =
        document.documentElement.getAttribute("data-accessibility") === "on";
      const newAccessibility = isAccessibilityOn ? "off" : "on";
      document.documentElement.setAttribute(
        "data-accessibility",
        newAccessibility,
      );
      localStorage.setItem("accessibility", newAccessibility);

      if (newAccessibility === "on") {
        if (accessibilityIcon) {
          accessibilityIcon.classList.remove("fa-universal-access");
          accessibilityIcon.classList.add("fa-eye-slash");
        }
        accessibilityToggle.setAttribute("title", "Disable Accessibility Mode");
      } else {
        if (accessibilityIcon) {
          accessibilityIcon.classList.remove("fa-eye-slash");
          accessibilityIcon.classList.add("fa-universal-access");
        }
        accessibilityToggle.setAttribute("title", "Enable Accessibility Mode");
      }
    });
  }
})();

function updateThemedImages(isDark) {
  const themedContainers = document.querySelectorAll(".vehicle-image");
  themedContainers.forEach((container) => {
    const img = container.querySelector("img");
    if (!img) return;
    const newSrc = isDark ? img.dataset.imgDark : img.dataset.imgLight;
    if (newSrc) {
      img.src = newSrc;
    }
  });
}
