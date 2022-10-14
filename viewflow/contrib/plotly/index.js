/* eslint-env browser */
import './index.scss';

export class VDash extends HTMLElement {
  connectedCallback() {
    this.renderer = new window.DashRenderer();
    window.addEventListener('turbo:before-render', this.onPageChange);
  }

  disconnectedCallback() {
    window.removeEventListener('turbo:before-render', this.onPageChange);
  }

  onPageChange = () => {
    this.renderer = null;
    window.ReactDOM.unmountComponentAtNode(document.getElementById('react-entry-point'));
  }
}

window.customElements.define('vf-dash-unmount', VDash);
