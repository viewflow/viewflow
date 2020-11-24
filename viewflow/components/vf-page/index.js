/* eslint-env browser */
import './index.scss';

import Turbolinks from 'turbolinks';
import {drawer, topAppBar} from 'material-components-web';
import {div} from '../vf-field/jhtml';

export class VPage extends HTMLElement {
  connectedCallback() {
    this._reconcileDrawerFrame = 0;
    this._mdcDrawer = null;
    this._topAppBar = null;

    this._drawerEl = this.querySelector('.vf-page__menu');
    this._contentEl = this.querySelector('.vf-page__body');
    this._toggleMenuEl = this.querySelector('.vf-page__menu-toggle-button');
    this._topAppBarEl = this.querySelector('.vf-page__body-toolbar');
    this._scrimEl = div({class: 'mdc-drawer-scrim'}).toDOM();

    if (window.innerWidth >= 992) {
      this._drawerEl.classList.toggle(
          'mdc-drawer--open',
          sessionStorage.getItem('viewflow_site_drawer_state') != 'closed',
      );
    }

    this._toggleMenuEl.addEventListener('click', this.onToggleMenuClick);
    window.addEventListener('resize', this.onWindowResize);

    this._mdcDrawer = drawer.MDCDrawer.attachTo(this._drawerEl);
    this._topAppBar = topAppBar.MDCTopAppBar.attachTo(this._topAppBarEl);
    this._topAppBar.setScrollTarget(this.querySelector('.vf-page__content'));
    this._topAppBar.listen('MDCTopAppBar:nav', (event) => {
      event.preventDefault();
      this.open = !this.open;
    });

    this.reconcileDrawer();
  }

  disconnectedCallback() {
    window.removeEventListener('resize', this.onWindowResize);
    this._toggleMenuEl.removeEventListener('click', this.onToggleMenuClick);
    if (this._mdcDrawer) {
      this._mdcDrawer.destroy();
    }
    if (this._topAppBar) {
      this._topAppBar.destroy();
    }
  }

  onWindowResize = () => {
    cancelAnimationFrame(this._reconcileDrawerFrame);
    this._reconcileDrawerFrame = requestAnimationFrame(() => this.reconcileDrawer());
  }

  onToggleMenuClick = (event) => {
    event.preventDefault();
    this.classList.toggle('vf-page__menu--secondary-open');
  }

  reconcileDrawer() {
    const rootClasses = this._drawerEl.classList;

    if (window.innerWidth < 992 && !rootClasses.contains('mdc-drawer--modal')) {
      this._mdcDrawer.destroy();
      this._drawerEl.classList.remove('mdc-drawer--dismissible');
      this._drawerEl.classList.remove('mdc-drawer--open');
      this._drawerEl.classList.add('mdc-drawer--modal');
      this.insertBefore(this._scrimEl, this._contentEl);
      this._contentEl.classList.remove('mdc-drawer-app-content');
      this._mdcDrawer = drawer.MDCDrawer.attachTo(this._drawerEl);
    } else if (window.innerWidth >= 992 && !rootClasses.contains('mdc-drawer--dismissible')) {
      this._mdcDrawer.destroy();
      this._drawerEl.classList.remove('mdc-drawer--modal');
      this._scrimEl.remove();
      this._drawerEl.classList.add('mdc-drawer--dismissible');
      this._contentEl.classList.add('mdc-drawer-app-content');
      this._drawerEl.classList.toggle(
          'mdc-drawer--open',
          sessionStorage.getItem('viewflow_site_drawer_state') != 'closed',
      );
      this._mdcDrawer = drawer.MDCDrawer.attachTo(this._drawerEl);
    }
  }

  get open() {
    if (this._mdcDrawer) {
      return this._mdcDrawer.open;
    }
  }

  set open(value) {
    if (this._mdcDrawer) {
      if (window.innerWidth >= 992) {
        sessionStorage.setItem('viewflow_site_drawer_state', value?'open':'closed');
      }
      return this._mdcDrawer.open = value;
    }
  }
}

export class VPageMenuToggle extends HTMLElement {
  connectedCallback() {
    setTimeout(() => {
      this._pageMenu = document.querySelector('vf-page-menu');
      this.addEventListener('click', this.onClick);
    });
  }

  disconnectedCallback() {
    this.removeEventListener('click', this.onClick);
  }

  onClick = (event) => {
    event.preventDefault();
    this._pageMenu.open = !this._pageMenu.open;
  }
}

export class VPageMenuNavigation extends HTMLElement {
  connectedCallback() {
    if (this.children.length) {
      this.activate();
    } else {
      setTimeout(this.activate);
    }
  }

  activate = () => {
    let currentPath = window.location.pathname;
    if (Turbolinks.controller.currentVisit && Turbolinks.controller.currentVisit.redirectedToLocation) {
      currentPath = Turbolinks.controller.currentVisit
          .redirectedToLocation.absoluteURL.substring(
              window.location.origin.length,
          );
    }

    const navItems = [].slice.call(
        this.querySelectorAll('.mdc-list-item:not(.vf-page-navigation__ignore)'),
    ).filter(
        (node) => currentPath.startsWith(node.pathname),
    );

    navItems.sort((a, b) => b.pathname.length - a.pathname.length);

    if (navItems.length) {
      navItems[0].classList.add('mdc-list-item--selected');
    }
  }
}

export class VPageScrollFix extends HTMLElement {
  connectedCallback() {
    this._reconcileBodyFrame = 0;
    this._clientWidth = document.body.clientWidth;
    this._gap = 0;

    window.addEventListener('resize', this.onResize);
    this._observer = new MutationObserver(this.onBodyChanged);
    this._observer.observe(document.body, {attributes: true, attributeFilter: ['class']});
  }

  disconnectedCallback() {
    window.removeEventListener('resize', this.onResize);
    cancelAnimationFrame(this._reconcileBodyFrame);
    this._observer.disconnect();
  }

  onResize = () => {
    if (!document.body.style.width) {
      this._clientWidth = document.body.clientWidth;
    } else {
      cancelAnimationFrame(this._reconcileBodyFrame);
      this._reconcileBodyFrame = requestAnimationFrame(() => {
        document.body.style.width = (window.innerWidth - this._gap) + 'px';
      });
    }
  }

  onBodyChanged = (mutationsList) => {
    const overflow = window.getComputedStyle(document.body).overflow;

    if (overflow == 'hidden') {
      this._gap = window.innerWidth - this._clientWidth;
      document.body.style.width = this._clientWidth + 'px';
    } else {
      document.body.style.removeProperty('width');
      this._clientWidth = document.body.clientWidth;
    }
  }
}
