/* eslint-env node */
const render = (ctx) => `{
  "name": "${ctx.project}",
  "version": "1.0.0",
  "description": "",
  "scripts": {
    "eslint": "eslint components/",
    "build": "rollup -c && NODE_ENV=production rollup -c",
    "watch": "rollup -w -c"
  },
  "keywords": [],
  "author": "",
  "license": "UNLICENSED",
  "devDependencies": {
    "@babel/core": "^7.10.5",
    "@babel/eslint-parser": "^7.12.17",
    "@babel/plugin-proposal-class-properties": "^7.10.4",
    "@babel/preset-env": "^7.10.4",
    "@babel/runtime": "7.12.13",
    "@rollup/plugin-babel": "^5.3.0",
    "@rollup/plugin-node-resolve": "^11.2.0",
    "eslint": "^7.20.0",
    "eslint-config-google": "^0.14.0",
    "eslint-plugin-babel": "^5.3.1",
    "rollup": "^2.21.0",
    "rollup-plugin-copy": "^3.3.0",
    "rollup-plugin-sass": "^1.2.2",
    "rollup-plugin-terser": "^7.0.2",
    "sass": "^1.32.7"
  },
  "browserslist": "> 5%",
  "babel": {
  },
  "eslintConfig": {
    "extends": "google",
    "parser": "@babel/eslint-parser",
    "parserOptions": {
      "classes": true,
      "ecmaVersion": 2017,
      "sourceType": "module"
    },
    "plugins": [
      "babel"
    ],
    "rules": {
      "require-jsdoc": "off",
      "max-len": [
        "error",
        120
      ],
      "no-undef": "error",
      "no-invalid-this": 0,
      "babel/no-invalid-this": 1
    },
    "env": {
      "es6": true
    }
  }
}
`.trimLeft();

exports.default = render;
