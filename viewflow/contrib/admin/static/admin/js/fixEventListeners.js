let eventName = 'turbo:render';
if (document.startViewTransition) {
  eventName = 'viewflow:render'
}

window.addEventListener("turbo:before-render", (event) => {
  if (document.startViewTransition) {
    const originalRender = event.detail.render
    event.detail.render = (currentElement, newElement) => {
      document.startViewTransition(async ()=> {
        await originalRender(currentElement, newElement);
        window.dispatchEvent(new Event('viewflow:render'));
      })
    }
  }
})

window.addEventListener(eventName, function() {
    const toggleNavSidebar = document.getElementById('toggle-nav-sidebar');
    if (toggleNavSidebar !== null) {
        const navSidebar = document.getElementById('nav-sidebar');
        const main = document.getElementById('main');
        let navSidebarIsOpen = localStorage.getItem('django.admin.navSidebarIsOpen');
        if (navSidebarIsOpen === null) {
            navSidebarIsOpen = 'true';
        }
        main.classList.toggle('shifted', navSidebarIsOpen === 'true');
        navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);

        toggleNavSidebar.addEventListener('click', function() {
            if (navSidebarIsOpen === 'true') {
                navSidebarIsOpen = 'false';
            } else {
                navSidebarIsOpen = 'true';
            }
            localStorage.setItem('django.admin.navSidebarIsOpen', navSidebarIsOpen);
            main.classList.toggle('shifted');
            navSidebar.setAttribute('aria-expanded', navSidebarIsOpen);
        });
    }
    window.initSidebarQuickFilter();
})

const originalAddEventListener = window.addEventListener;

window.addEventListener = function(event, listener, options) {
  if (event === 'load') {
    originalAddEventListener.call(this, eventName, listener, options);
  }

  originalAddEventListener.call(this, event, listener, options);
};


const originalDocAddEventListener = document.addEventListener;

document.addEventListener = function(event, listener, options) {
  if (event === 'DOMContentLoaded') {
    originalDocAddEventListener.call(this, eventName, listener, options);
  }

  originalDocAddEventListener.call(this, event, listener, options);
};


document.addEventListener('turbo:before-fetch-request', (event) => {
    // set the mark for `viewflow.middleware.HotwireTurboMiddleware` request codes substitution
    event.detail.fetchOptions.headers['X-Request-Framework'] = 'Turbo';
  }
);

