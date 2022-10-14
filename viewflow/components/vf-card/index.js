/* eslint-env browser */
import './index.scss';

import {MDCMenu} from '@material/menu';


export class VCardMenu extends HTMLElement {
  connectedCallback() {
    setTimeout(() => {
      this._menuEl = this.querySelector('.mdc-menu');
      this._triggerEl = this.querySelector('.vf-card__menu-trigger');

      this._mdcMenu = new MDCMenu(this._menuEl);
      this._menuEl.addEventListener('MDCMenu:selected', this.onMenuSelect);
      this._triggerEl.addEventListener('click', this.onToggleMenu);
    });
  }

  disconnectedCallback() {
    if(this._mdcMenu) {
      this._mdcMenu.destroy();
    }
    if(this._triggerEl) {
      this._triggerEl.removeEventListener('click', this.onToggleMenu);
    }
  }

  onToggleMenu = () => {
    this._mdcMenu.open = !this._mdcMenu.open;
  }

  onMenuSelect = (event) => {
    event.preventDefault();
    const itemData = event.detail.item.dataset;
    if (itemData.cardMenuHref) {
      if (window.Turbo) {
        window.Turbo.visit(itemData.cardMenuHref);
      } else {
        window.location = itemData.cardMenuHref;
      }
    }
  }
}
