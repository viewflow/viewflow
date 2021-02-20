/* eslint-env node */
const render = (ctx) => `my-component {
  &:hover {
    color: red;
  }
}
`.trimLeft();

exports.default = render;
