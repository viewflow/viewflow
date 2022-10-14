/* eslint-env browser */

export class VFPageReload extends HTMLElement {
  connectedCallback() {
    const url = new URL(window.location.href);
    const reloadAttempts = 1 + (parseInt(url.searchParams.get('_reload_attempts')) || 0);
    url.searchParams.set('_reload_attempts', reloadAttempts);

    this.timeoutId = setTimeout(() => {
      window.Turbo.visit(url.toString());
    }, reloadAttempts < 2 ? 2000: 5000);
  }

  disconnectedCallback() {
    clearTimeout(this.timeoutId);
  }
}
