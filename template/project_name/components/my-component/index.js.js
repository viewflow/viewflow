/* eslint-env node */
const render = (ctx) => `/* eslint-env browser */
import './index.scss';

export class MyComponent extends HTMLElement {
  connectedCallback() {
  }

  disconnectedCallback() {
  }
}
`.trimLeft();

exports.default = render;
