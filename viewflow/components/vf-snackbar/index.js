/* eslint-env browser */

import {snackbar} from 'material-components-web';
import {div, a} from '../vf-field/jhtml';

export class VSnackbar extends HTMLElement {
  connectedCallback() {
    setTimeout(() => {
      window.addEventListener('vf-snackbar:show', this.onShowSnackbarEvent, false);
      this._showInitialSnackbar();
    });
  }

  disconnectedCallback() {
    if (this._mdcSnackbar) {
      this._mdcSnackbar.destroy();
    }
    window.removeEventListener('vf-snackbar:show', this.onShowSnackbarEvent);
  }

  onShowSnackbarEvent = (event) => {
    this._showSnackBar(event.detail.message, event.detail.actionText, event.detail.actionLink);
  }

  _showSnackBar(message, actionText, actionLink) {
    const surface = div({class: 'mdc-snackbar__surface'}).with([
      div({class: 'mdc-snackbar__label'}).text(message),
      actionText ?
        div({class: 'mdc-snackbar__actions'}).with([
          a({class: 'mdc-button mdc-snackbar__action', href: actionLink}).text(actionText),
        ]) :
        null,
    ]);

    if (this._mdcSnackbar) {
      this._mdcSnackbar.destroy();
    }

    this.innerHTML = surface.toDOM().outerHTML;
    this._mdcSnackbar = snackbar.MDCSnackbar.attachTo(this);
    this._mdcSnackbar.open();
  }

  _showInitialSnackbar() {
    let actionText;
    // let actionHandler;

    const message = Array.prototype.filter.call(this.childNodes, (child) => {
      return child.nodeType === Node.TEXT_NODE;
    }).map((child) => {
      return child.textContent.trim();
    }).join(' ');

    const link = this.querySelector('a');
    if (link && window.location.href !== link.href) {
      actionText = link.textContent;
    }

    if (message) {
      this._showSnackBar(message, actionText, link ? link.href : null);
    }
  }
};
