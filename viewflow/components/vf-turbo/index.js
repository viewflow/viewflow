/* eslint-env browser */
import './index.scss';

export class VTurbo extends HTMLElement {
  connectedCallback() {
    document.addEventListener('turbo:before-fetch-request', this.onBeforeTurboFetch);
    document.addEventListener('turbo:before-fetch-response', this.disableTurboOnError);
  }

  disconnectedCallback() {
    document.removeEventListener('turbo:before-fetch-request', this.onBeforeTurboFetch);
    document.removeEventListener('turbo:before-fetch-response', this.disableTurboOnError);
  }

  onBeforeTurboFetch = (event) => {
    // set the mark for `viewflow.middleware.HotwireTurboMiddleware` request codes substitution
    event.detail.fetchOptions.headers['X-Request-Framework'] = 'Turbo';
  }

  disableTurboOnError = (event) => {
    if(event.detail.fetchResponse.response.status>400) {
      Turbo.session.drive = false;
      window.onpopstate = () => {
        window.location = window.location;
      }

    }
  }
}


// tidi Turbo.session.drive = false
