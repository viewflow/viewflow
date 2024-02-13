import { defineConfig } from 'vite'
import solidPlugin from 'vite-plugin-solid';
import { viteStaticCopy } from 'vite-plugin-static-copy';


const copyTargets = [
  {
    src: [
      `node_modules/shepherd.js/dist/js/shepherd.min.js`,
      `node_modules/shepherd.js/dist/js/shepherd.min.js.map`,
      `node_modules/js-cookie/dist/js.cookie.min.js`
    ],
    dest: '../../../demo/static/demo/js/',
  },
  {
    src: `node_modules/shepherd.js/dist/css/shepherd.css`,
    dest: '../../../demo/static/demo/css/',
  },
  {
    src: [
      'node_modules//@hotwired/turbo/dist/turbo.es2017-umd.js',
      `node_modules/perfect-scrollbar/dist/perfect-scrollbar.min.js`,
      `node_modules/perfect-scrollbar/dist/perfect-scrollbar.min.js.map`,
      `node_modules/trix/dist/trix.js`,
      'node_modules/smartcrop/smartcrop.js',
      `node_modules/vis-network/dist/vis-network.min.js`,
      `node_modules/vis-network/dist/vis-network.min.js.map`,
    ],
    dest: 'js/',
  },
  {
    src: [
      'node_modules/perfect-scrollbar/css/perfect-scrollbar.css',
      `node_modules/vis-network/dist/dist/vis-network.min.css`,
      `node_modules/trix/dist/trix.css`,
    ],
    dest: 'css/',
  },
  {
    src: [
      `node_modules/material-icons/iconfont/*.woff`,
      `node_modules/material-icons/iconfont/*.woff2`,
      `node_modules/material-icons/iconfont/material-icons.css`,
    ],
    dest: 'fonts/material-icons/',
  },
  {
    src: `node_modules/roboto-fontface/fonts/roboto/*`,
    dest: 'fonts/roboto/',
  },
  {
    src: `node_modules/roboto-fontface/css/roboto/roboto-fontface.css`,
    dest: 'fonts/roboto/',
    transform: (content) => content.toString().replace(/\.\.\/\.\.\/fonts\/roboto\//g, './'),
  },
  {
    src: `node_modules/simple-icons-font/font/*`,
    dest: 'fonts/simple-icons/',
  },
]

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [solidPlugin(), viteStaticCopy({targets: copyTargets})],
  build: {
    sourcemap: true,
    emptyOutDir: false,
    outDir: 'viewflow/static/viewflow/',
    lib: {
      entry: 'viewflow/components/index.ts',
      formats: ['iife'],
      name: 'viewflow',
      fileName: () => "viewflow.min.js",
    },
    rollupOptions: {
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name == "style.css")
            return "css/viewflow.min.css";
          return assetInfo.name;
        },
        entryFileNames: "js/viewflow.min.js",
      },
      // external: /^lit/
    }
  }
})
