/* eslint-env browser */
import './vf-page-lockscreen';

import {VCardMenu} from './vf-card';
import {VPage, VPageMenuToggle, VPageMenuNavigation, VPageScrollFix} from './vf-page';
import {VPerfectScroll} from './vf-perfect-scroll';
import {VSnackbar} from './vf-snackbar';
import {VTurbolinks} from './vf-turbolinks';

window.addEventListener('DOMContentLoaded', () => {
  window.customElements.define('vf-card-menu', VCardMenu);
  window.customElements.define('vf-page-menu-navigation', VPageMenuNavigation);
  window.customElements.define('vf-page-menu-toggle', VPageMenuToggle);
  window.customElements.define('vf-page-scroll-fix', VPageScrollFix);
  window.customElements.define('vf-page', VPage);
  window.customElements.define('vf-perfect-scroll', VPerfectScroll);
  window.customElements.define('vf-snackbar', VSnackbar);
  window.customElements.define('vf-turbolinks', VTurbolinks);
});
