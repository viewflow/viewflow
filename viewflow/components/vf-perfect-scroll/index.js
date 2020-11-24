/* eslint-env browser */
import PerfectScrollbar from 'perfect-scrollbar';


export class VPerfectScroll extends HTMLElement {
  connectedCallback() {
    this.scroll = new PerfectScrollbar(this.parentElement);
  }

  disconnectedCallback() {
    this.scroll.destroy();
  }
}
