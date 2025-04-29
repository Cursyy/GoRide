document.addEventListener("DOMContentLoaded", function () {
  gsap.registerPlugin(ScrollTrigger);

  gsap.utils.toArray(".animate-on-scroll").forEach((element) => {
    gsap.fromTo(
      element,
      { opacity: 0, y: 50 },
      {
        opacity: 1,
        y: 0,
        duration: 0.8,
        ease: "power3.out",
        scrollTrigger: {
          trigger: element,
          start: "top 85%",
          toggleActions: "play none none none",
          once: true,
        },
      },
    );
  });

  const stickySections = gsap.utils.toArray(".sticky-section");

  stickySections.forEach((section, index, sections) => {
    const contentWrapper = section.querySelector(".content-wrapper");

    if (index < sections.length - 1) {
      const nextSection = sections[index + 1];

      gsap.to(contentWrapper, {
        opacity: 0,
        filter: "blur(8px)",
        scale: 0.95,
        ease: "power1.in",
        scrollTrigger: {
          trigger: nextSection,
          start: "top bottom-=10%",
          end: "top center",
          scrub: 0.5,
        },
      });
    }
  });

  const contactForm = document.getElementById("contactForm");
  if (contactForm) {
    contactForm.addEventListener("submit", function (event) {});
  }
});
