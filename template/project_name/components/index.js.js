/* eslint-env node */
const render = (ctx) => `/* eslint-env browser */
import {MyComponent} from './my-component';

window.addEventListener('DOMContentLoaded', () => {
  window.customElements.define('my-component', MyComponent);
});
`.trimLeft();

exports.default = render;
