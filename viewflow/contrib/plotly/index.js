/* eslint-env browser */
import './index.scss';

export class VDash extends HTMLElement {
  connectedCallback() {
    this.start()
    window.addEventListener('turbo:before-render', this.onPageChange);
  }

  start() {
    if(!window.DashRenderer || !window.dash_html_components) {
      setTimeout(() => this.start(), 300)
    } else {
      this.renderer = new window.DashRenderer();
    }
  }

  disconnectedCallback() {
    window.removeEventListener('turbo:before-render', this.onPageChange);
  }

  onPageChange = () => {
    this.renderer = null;
    // window.ReactDOM.unmountComponentAtNode(document.getElementById('react-entry-point'));
  }
}

window.customElements.define('vf-dash-unmount', VDash);
