// static/js/theme-change.js // Назву файлу краще без підкреслень

(function () {
  const themeToggleButton = document.getElementById("theme-toggle");
  const themeIcon = document.getElementById("theme-icon");
  // Перевіряємо наявність елементів перед роботою з ними
  if (!themeToggleButton || !themeIcon) {
    console.warn("Theme toggle button or icon not found.");
    // return; // Можна вийти, якщо кнопки немає
  }

  const prefersDarkScheme = window.matchMedia("(prefers-color-scheme: dark)");

  // Функція для встановлення теми (тепер працює з <html>)
  function setTheme(isDark) {
    const rootElement = document.documentElement; // Ціль - <html>
    if (isDark) {
      rootElement.classList.add("dark-mode");
      if (themeIcon) {
        // Перевіряємо ще раз, чи існує іконка
        themeIcon.classList.remove("fa-sun");
        themeIcon.classList.add("fa-moon");
      }
      localStorage.setItem("theme", "dark");
      if (themeToggleButton)
        themeToggleButton.setAttribute("title", "Switch to light theme"); // Оновлюємо title кнопки
    } else {
      rootElement.classList.remove("dark-mode");
      if (themeIcon) {
        // Перевіряємо ще раз, чи існує іконка
        themeIcon.classList.remove("fa-moon");
        themeIcon.classList.add("fa-sun");
      }
      localStorage.setItem("theme", "light");
      if (themeToggleButton)
        themeToggleButton.setAttribute("title", "Switch to dark theme"); // Оновлюємо title кнопки
    }
  }

  // --- Перевірка початкової теми (виконується скриптом у <head>) ---
  // Цей блок можна закоментувати або видалити, якщо скрипт у <head> працює надійно
  /*
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'dark') {
        setTheme(true);
    } else if (currentTheme === 'light') {
        setTheme(false);
    } else {
        setTheme(prefersDarkScheme.matches);
    }
    */
  // Оновимо іконку та title кнопки на основі стану, встановленого скриптом у <head>
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

  // --- Обробник події для кнопки ---
  if (themeToggleButton) {
    themeToggleButton.addEventListener("click", () => {
      // Перемикаємо тему на основі поточного стану <html>
      setTheme(!document.documentElement.classList.contains("dark-mode"));
    });
  }

  // --- Слухач зміни системних налаштувань ---
  prefersDarkScheme.addEventListener("change", (e) => {
    // Застосовуємо зміну, тільки якщо користувач не робив явного вибору
    if (!localStorage.getItem("theme")) {
      setTheme(e.matches);
    }
  });
})();
