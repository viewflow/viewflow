/* eslint-env browser */
import './vf-modal-trigger.scss';


export class VFModalTrigger extends HTMLElement {
  connectedCallback() {
    this._contentEl = this.querySelector('.vf-modal-trigger__content');
    this._buttonEl = this.querySelector('.vf-modal-trigger__button');

    this.addEventListener('click', this.onCloseDialog);
    this._contentEl.addEventListener('keydown', this.onOpenDialog);
    this._contentEl.addEventListener('click', this.onOpenDialog);
    this._buttonEl.addEventListener('click', this.onCloseDialog);
  }

  disconnectedCallback() {
    this.removeEventListener('click', this.onCloseDialog);
    this._contentEl.removeEventListener('click', this.onOpenDialog);
    this._contentEl.removeEventListener('keydown', this.onOpenDialog);
    this._buttonEl.removeEventListener('click', this.onOpenDialog);
  }

  onOpenDialog = (event) => {
    if (!this.classList.contains('vf-modal-trigger--open')) {
      if (event.type == 'click' || event.keyCode == 13 || event.keyCode == 20) {
        this.classList.add('vf-modal-trigger--open');
      }
    } else if (event.keyCode == 27) {
      this.classList.remove('vf-modal-trigger--open');
    }
    event.stopPropagation();
  }

  onCloseDialog = (event) => {
    this.classList.remove('vf-modal-trigger--open');
    event.stopPropagation();
  }
}
