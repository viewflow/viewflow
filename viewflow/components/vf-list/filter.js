/* eslint-env browser */
import {drawer} from 'material-components-web';
import {div} from '../vf-field/jhtml';


export class VListFilter extends HTMLElement {
  connectedCallback() {
    this._reconcileDrawerFrame = 0;
    this._mdcDrawer = null;
    this._contentEl = document.querySelector('main .vf-page__grid');
    this._scrimEl = div({class: 'mdc-drawer-scrim'}).toDOM();

    this._pagePath = window.location.pathname;
    this._persistentStateVar = `v_list_filter_` + this._pagePath.replace(/\//g, '_') + this.id;
    this._persistentOpen = window.sessionStorage.getItem(this._persistentStateVar);
    if (window.innerWidth >= 992) {
      if (this._persistentOpen === null) {
        this._persistentOpen = this.classList.contains('mdc-drawer--open');
      } else {
        this.classList.toggle('mdc-drawer--open', this._persistentOpen);
      }
    } else {
      this.classList.remove('mdc-drawer--open');
    }

    this._mdcDrawer = drawer.MDCDrawer.attachTo(this);

    setTimeout(() => {
      window.addEventListener('turbo:load', this.onPageChange);
      window.addEventListener('resize', this.onWindowResize);
      this.reconcileDrawer();
    });
  }

  disconnectedCallback() {
    window.removeEventListener('turbo:load', this.onPageChange);
    window.removeEventListener('resize', this.onWindowResize);
    if (this._mdcTemporalDrawer) {
      this._mdcTemporalDrawer.destroy();
    }
    if (this._mdcPersistentDrawer) {
      this._mdcPersistentDrawer.destroy();
    }
  }

  onWindowResize = () => {
    cancelAnimationFrame(this._reconcileDrawerFrame);
    this._reconcileDrawerFrame = requestAnimationFrame(() => this.reconcileDrawer());
  }

  onPageChange = () => {
    if (this._pagePath !== window.location.pathname) {
      window.sessionStorage.removeItem(this._persistentStateVar);
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
        window.sessionStorage.setItem(this._persistentStateVar, value?'open':'');
      }
      return this._mdcDrawer.open = value;
    }
  }

  reconcileDrawer() {
    const rootClasses = this.classList;

    if (window.innerWidth < 992 && !rootClasses.contains('mdc-drawer--modal')) {
      this._mdcDrawer.destroy();
      this.classList.remove('mdc-drawer--dismissible');
      this.classList.remove('mdc-drawer--open');
      this.classList.add('mdc-drawer--modal');
      this.parentElement.insertBefore(this._scrimEl, this._contentEl);
      this._contentEl.classList.remove('mdc-drawer-app-content');
      this._mdcDrawer = drawer.MDCDrawer.attachTo(this);
    } else if (window.innerWidth >= 992 && !rootClasses.contains('mdc-drawer--dismissible')) {
      this._mdcDrawer.destroy();
      this.classList.remove('mdc-drawer--modal');
      this._scrimEl.remove();
      this.classList.add('mdc-drawer--dismissible');
      this._contentEl.classList.add('mdc-drawer-app-content');
      this.classList.toggle('mdc-drawer--open', sessionStorage.getItem('viewflow_site_drawer_state') != 'closed');
      this._mdcDrawer = drawer.MDCDrawer.attachTo(this);
    }
  }
}

export class VListFilterTrigger extends HTMLElement {
  connectedCallback() {
    setTimeout(() => {
      this._drawerEl = document.getElementById(this.dataset.toggleFilterId);
      this.addEventListener('click', this.onToggleDrawerClick);
    });
  }

  disconnectedCallback() {
    this.removeEventListener('click', this.onToggleDrawerClick);
  }

  onToggleDrawerClick = (event) => {
    event.preventDefault();
    document.querySelector('.vf-page__body').style.overflow='hidden';
    this._drawerEl.open = !this._drawerEl.open;
    setTimeout(() => {
      document.querySelector('.vf-page__body').style.overflow=null;
    }, 300);
  }
}

