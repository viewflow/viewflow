/* eslint-env node */
const render = (ctx) => `/* eslint-env node */
import { babel } from '@rollup/plugin-babel';
import { terser } from "rollup-plugin-terser";
import copy from 'rollup-plugin-copy';
import resolve from '@rollup/plugin-node-resolve';
import sass from 'rollup-plugin-sass';

const PROD = process.env.NODE_ENV === 'production';
const FILE_SUFFIX = PROD ? '.min': '';

export default {
  input: 'components/index.js',
  output: {
    name: '${ctx.project}',
    file: \`static/${ctx.project}/js/${ctx.project}-components\${FILE_SUFFIX}.js\`,
    sourcemap: PROD,
    format: 'iife',
    globals: {},
  },
  external: [],
  plugins: [
    sass({
      output: \`static/${ctx.project}/css/${ctx.project}-components\${FILE_SUFFIX}.css\`,
      options: {
        includePaths: [
          'node_modules',
        ],
        outputStyle: PROD ? 'compressed': 'expanded',
      },
    }),
    resolve(),
    babel({
      exclude: 'node_modules/**',
      presets: ['@babel/preset-env'],
      plugins: ["@babel/plugin-proposal-class-properties"],
      babelHelpers: 'inline',
    }),
    (PROD && terser()),
    copy({
      targets: [
        // {
        //   src: \`node_modules/material-components-web/dist/material-components-web\${FILE_SUFFIX}.js\`,
        //   dest: 'static/${ctx.project}/js/',
        // }
      ]
    }),
  ],
}
`.trimLeft();

exports.default = render;
