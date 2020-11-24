/* eslint-env browser */
import './index.scss';

import Turbolinks from 'turbolinks';
import {menu} from 'material-components-web';

export class VCardMenu extends HTMLElement {
  connectedCallback() {
    setTimeout(() => {
      this._menuEl = this.querySelector('.mdc-menu');
      this._triggerEl = this.querySelector('.vf-card__menu-trigger');

      this._mdcMenu = new menu.MDCMenu(this._menuEl);
      this._menuEl.addEventListener('MDCMenu:selected', this.onMenuSelect);
      this._triggerEl.addEventListener('click', this.onToggleMenu);
    });
  }

  disconnectedCallback() {
    this._mdcMenu.destroy();
    this._triggerEl.removeEventListener('click', this.onToggleMenu);
  }

  onToggleMenu = () => {
    this._mdcMenu.open = !this._mdcMenu.open;
  }

  onMenuSelect = (event) => {
    event.preventDefault();
    const itemData = event.detail.item.dataset;
    if (itemData.cardMenuHref) {
      if (Turbolinks) {
        Turbolinks.visit(itemData.cardMenuHref);
      } else {
        window.location = itemData.cardMenuHref;
      }
    }
  }
}
