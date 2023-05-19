/* eslint-env browser */
import './_grid.scss';
import './_menu.scss';
import './index.scss';

import {drawer, topAppBar, textField, dialog} from 'material-components-web';
import {customElement} from 'solid-element';
import {createSignal, createEffect} from 'solid-js';
import {div} from '../vf-field/jhtml';
import cc from 'classcat';


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

    if (!this._drawerEl) return;

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
    if (!this._drawerEl) return;

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
  };

  onToggleMenuClick = (event) => {
    event.preventDefault();
    this.classList.toggle('vf-page__menu--secondary-open');
  };

  reconcileDrawer() {
    const rootClasses = this._drawerEl.classList;

    if (window.innerWidth < 992 && !rootClasses.contains('mdc-drawer--modal')) {
      if (this._mdcDrawer) {
        this._mdcDrawer.destroy();
      }
      this._drawerEl.classList.remove('mdc-drawer--dismissible');
      this._drawerEl.classList.remove('mdc-drawer--open');
      this._drawerEl.classList.add('mdc-drawer--modal');
      this.insertBefore(this._scrimEl, this._contentEl);
      this._contentEl.classList.remove('mdc-drawer-app-content');
      this._mdcDrawer = drawer.MDCDrawer.attachTo(this._drawerEl);
    } else if (window.innerWidth >= 992 && !rootClasses.contains('mdc-drawer--dismissible')) {
      if (this._mdcDrawer) {
        this._mdcDrawer.destroy();
      }
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
  };
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
    // TODO: try to perform this on visit complete, to get current path without currentVisit trick
    const Turbo = window.Turbo;
    let currentPath = window.location.pathname;

    if (Turbo.navigator.currentVisit && Turbo.navigator.currentVisit.redirectedToLocation) {
      currentPath = Turbo.navigator.currentVisit
          .redirectedToLocation.href.substring(
              window.location.origin.length,
          );
    } else if (Turbo.navigator.currentVisit && Turbo.navigator.currentVisit.location) {
      currentPath = Turbo.navigator.currentVisit
          .location.href.substring(
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
  };
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
  };

  onBodyChanged = (mutationsList) => {
    const overflow = window.getComputedStyle(document.body).overflow;

    if (overflow == 'hidden') {
      this._gap = window.innerWidth - this._clientWidth;
      document.body.style.width = this._clientWidth + 'px';
    } else {
      document.body.style.removeProperty('width');
      this._clientWidth = document.body.clientWidth;
    }
  };
}


export const VPageSearch = customElement('vf-page-search', {value: '', active: false}, (props, {element}) => {
  let control;
  let textfield;
  Object.defineProperty(element, 'renderRoot', {value: element});
  const [active, setActive] = createSignal(!!props.value);

  createEffect(() => {
    setTimeout(() => {
      textfield = new textField.MDCTextField(control);
      control.textfield=textfield;
      if (active()) {
        textfield.focus();
      }
    });
  });

  const getStartSection = () => {
    const parentRow = element.closest('.mdc-top-app-bar__row');
    return parentRow.querySelector('.mdc-top-app-bar__section--align-start');
  };

  if (!!props.value) {
    getStartSection().style.display = 'none';
  }

  const onBackClick = (event) => {
    getStartSection().style.removeProperty('display');

    const inputEl = element.querySelector('input');
    if (inputEl.value) {
      inputEl.value = '';
      element.querySelector('button[type=submit]').click();
    }
    setActive(false);
  };

  const onSearchClick = (event) => {
    if (!active()) {
      getStartSection().style.display = 'none';
      setActive(true);
      textfield.focus();
      event.preventDefault();
    }
  };


  return (
    <div class={'vf-page__search-container' + (active() ? ' vf-page__search-container--active':'')}>
      <button
        class="material-icons mdc-top-app-bar__navigation-icon mdc-icon-button vf-page__search-back-button"
        data-turbo="false"
        onClick={onBackClick}
      >arrow_back</button>
      <vf-form>
        <form method="GET">
          <label
            class={cc({
              'mdc-text-field': true,
              'mdc-text-field--filled': true,
              'mdc-text-field--label-floating': !!props.value,
            })}
            ref={control}>
            <span
              class={cc({
                'mdc-floating-label': true,
                'mdc-floating-label--float-above': !!props.value,
              })}
              id="id_page_search_label"
            >Search...</span>
            <input
              class="mdc-text-field__input"
              type="text" aria-labelledby="id_page_search_label"
              value={props.value}
              name="_search"/>
            <span class="mdc-line-ripple"></span>
          </label>
          <button
            class="material-icons mdc-top-app-bar__navigation-icon mdc-icon-button"
            type="submit"
            onClick={onSearchClick}
          >search</button>
        </form>
      </vf-form>
    </div>
  );
});


export class VDialog extends HTMLElement {
  connectedCallback() {
    this._dialogEl = this.querySelector('.mdc-dialog');
    this._triggerEl = this.querySelector('.vf-dialog__trigger');

    this._mdcDialog = new dialog.MDCDialog(this._dialogEl);
    this._triggerEl.addEventListener('click', this.onTriggerClick);

    this._mdcDialog.listen('MDCDialog:closed', () => {
      this._triggerEl.style.display = null;
    });
  }

  disconnectedCallback() {
    if (this._mdcDialog) {
      this._mdcDialog.destroy();
    }
    this._triggerEl.removeEventListener('click', this.onTriggerClick);
  }

  onTriggerClick = (event) => {
    event.preventDefault();
    this._mdcDialog.open();
    this._triggerEl.style.display = 'none';
  }
}
