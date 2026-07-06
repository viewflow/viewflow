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
    const status = event.detail.fetchResponse.response.status;
    // 422 is HotwireTurboMiddleware's own convention for a re-rendered
    // POST with form validation errors, not an actual error -- it must
    // not disable Turbo drive.
    if(status>400 && status !== 422) {
      Turbo.session.drive = false;
      window.addEventListener('popstate', () => {
        window.location = window.location;
      });
    }
  }
}


// tidi Turbo.session.drive = false
