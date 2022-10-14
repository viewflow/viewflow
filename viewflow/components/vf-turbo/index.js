/* eslint-env browser */
import './index.scss';

export class VTurbo extends HTMLElement {
  connectedCallback() {
    document.addEventListener('turbo:before-fetch-request', this.onBeforeTurboFetch);
  }

  disconnectedCallback() {
    document.removeEventListener('turbo:before-fetch-request', this.onBeforeTurboFetch);
  }

  onBeforeTurboFetch = (event) => {
    // set the mark for `viewflow.middleware.HotwireTurboMiddleware` request codes substitution
    event.detail.fetchOptions.headers['X-Request-Framework'] = 'Turbo';
  }
}
