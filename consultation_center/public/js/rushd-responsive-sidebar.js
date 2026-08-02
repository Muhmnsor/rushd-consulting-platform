document.addEventListener("DOMContentLoaded", () => {
	const sidebar = document.querySelector("[data-rushd-sidebar]");
	const toggle = document.querySelector("[data-rushd-sidebar-toggle]");
	const closeButton = document.querySelector("[data-rushd-sidebar-close]");
	const backdrop = document.querySelector("[data-rushd-sidebar-backdrop]");
	if (!sidebar || !toggle || !closeButton || !backdrop) return;

	const mobileViewport = window.matchMedia("(max-width: 1100px)");
	let lastTrigger = null;

	const setOpen = (open, restoreFocus = false) => {
		const shouldOpen = Boolean(open && mobileViewport.matches);
		document.body.classList.toggle("rushd-sidebar-open", shouldOpen);
		toggle.setAttribute("aria-expanded", shouldOpen ? "true" : "false");
		sidebar.setAttribute("aria-hidden", mobileViewport.matches && !shouldOpen ? "true" : "false");
		if (shouldOpen) {
			lastTrigger = document.activeElement;
			window.requestAnimationFrame(() => closeButton.focus());
		} else if (restoreFocus && lastTrigger instanceof HTMLElement) {
			lastTrigger.focus();
		}
	};

	toggle.addEventListener("click", () => {
		setOpen(!document.body.classList.contains("rushd-sidebar-open"));
	});
	closeButton.addEventListener("click", () => setOpen(false, true));
	backdrop.addEventListener("click", () => setOpen(false, true));
	sidebar.querySelectorAll("a").forEach((link) => {
		link.addEventListener("click", () => setOpen(false));
	});
	document.addEventListener("keydown", (event) => {
		if (event.key === "Escape" && document.body.classList.contains("rushd-sidebar-open")) {
			setOpen(false, true);
		}
	});
	mobileViewport.addEventListener("change", () => setOpen(false));
	setOpen(false);
});
