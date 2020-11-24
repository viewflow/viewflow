/* eslint-env node */
import babel from '@rollup/plugin-babel';
import commonjs from '@rollup/plugin-commonjs';
import copy from 'rollup-plugin-copy';
import minify from 'rollup-plugin-babel-minify';
import resolve from '@rollup/plugin-node-resolve';
import sass from 'rollup-plugin-sass';

const PROD = process.env.NODE_ENV === 'production';
const FILE_SUFFIX = PROD ? '.min': '';

const jsPlugins = [
  resolve(),
  commonjs({
    include: ['/node_modules/**'],
  }),
  babel({
    exclude: 'node_modules/**',
    presets: ['babel-preset-solid'],
    plugins: [
      ['@babel/plugin-proposal-class-properties', {'loose': false}],
    ],
    babelHelpers: 'inline',
    exclude: 'node_modules/**',
  }),
];

const vfComponents = {
  input: 'viewflow/components/viewflow-components.js',
  output: {
    name: 'viewflow',
    file: `viewflow/static/viewflow/js/viewflow-components${FILE_SUFFIX}.js`,
    sourcemap: true,
    format: 'iife',
    globals: {
      'material-components-web': 'mdc',
      'turbolinks': 'Turbolinks',
      'vis': 'vis',
      'perfect-scrollbar': 'PerfectScrollbar',
    },
  },
  external: ['vis', 'material-components-web', 'turbolinks'],
  plugins: [
    sass({
      output: `viewflow/static/viewflow/css/viewflow-components${FILE_SUFFIX}.css`,
      runtime: require('dart-sass'),
      options: {
        includePaths: [
          'node_modules',
        ],
        outputStyle: PROD ? 'compressed': 'expanded',
      },
    }),
    ...jsPlugins,
    copy({
      targets: [
        {
          src: `node_modules/material-components-web/dist/material-components-web${FILE_SUFFIX}.js`,
          dest: 'viewflow/static/viewflow/js/',
        },
        {
          src: `node_modules/material-components-web/dist/material-components-web${FILE_SUFFIX}.css`,
          dest: 'viewflow/static/viewflow/css/',
        },
        {
          src: 'node_modules/perfect-scrollbar/dist/perfect-scrollbar.min.js',
          dest: 'viewflow/static/viewflow/js/',
        },
        {
          src: 'node_modules/perfect-scrollbar/css/perfect-scrollbar.css',
          dest: 'viewflow/static/viewflow/css/',
        },
        {
          src: 'node_modules/turbolinks/dist/turbolinks.js',
          dest: 'viewflow/static/viewflow/js/',
        },
        {
          src: `node_modules/vis-network/dist/vis-network${FILE_SUFFIX}.js`,
          dest: 'viewflow/static/viewflow/js/',
        },
        {
          src: `node_modules/vis-network/dist/vis-network${FILE_SUFFIX}.css`,
          dest: 'viewflow/static/viewflow/css/',
        },
        {
          src: `node_modules/material-design-icons-iconfont/dist/fonts/*`,
          dest: 'viewflow/static/viewflow/fonts/material-design-icons/',
        },
        {
          src: `node_modules/material-design-icons-iconfont/dist/material-design-icons.css`,
          dest: 'viewflow/static/viewflow/fonts/material-design-icons/',
          transform: (content) => content.toString().replace(/\.\/fonts\//g, './'),
        },
        {
          src: `node_modules/roboto-fontface/fonts/roboto/*`,
          dest: 'viewflow/static/viewflow/fonts/roboto/',
        },
        {
          src: `node_modules/roboto-fontface/css/roboto/roboto-fontface.css`,
          dest: 'viewflow/static/viewflow/fonts/roboto/',
          transform: (content) => content.toString().replace(/\.\.\/\.\.\/fonts\/roboto\//g, './'),
        },
      ],
    }),
    (PROD && minify({mangle: false})),
  ],
};

const vfPageProfile = {
  input: 'viewflow/components/viewflow-page-profile.js',
  output: {
    name: 'viewflow',
    file: `viewflow/static/viewflow/js/viewflow-page-profile${FILE_SUFFIX}.js`,
    sourcemap: true,
    format: 'iife',
    globals: {
      'material-components-web': 'mdc',
      'turbolinks': 'Turbolinks',
    },
  },
  external: ['material-components-web', 'turbolinks'],
  plugins: [
    sass({
      output: `viewflow/static/viewflow/css/viewflow-page-profile${FILE_SUFFIX}.css`,
      runtime: require('dart-sass'),
      options: {
        includePaths: [
          'node_modules',
        ],
        outputStyle: PROD ? 'compressed': 'expanded',
      },
    }),
    ...jsPlugins,
    (PROD && minify({mangle: false})),
  ],
};

export default [
  vfComponents,
  vfPageProfile,
];
