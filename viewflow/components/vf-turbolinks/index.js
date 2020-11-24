/* eslint-env browser */
import Turbolinks from 'turbolinks';

export class VTurbolinks extends HTMLElement {
  connectedCallback() {
    document.addEventListener('turbolinks:request-end', this.onRequestEnd);
  }

  disconnectedCallback() {
    document.removeEventListener('turbolinks:request-end', this.onRequestEnd);
  }

  onRequestEnd = (event) => {
    if (event.data.xhr.status>=400) {
      Turbolinks.controller.disable();
    }
  }
}
