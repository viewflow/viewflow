/* eslint-env browser */

import './vf-django-admin.scss';
import {VFModalTrigger} from '../../components/vf-modal/vf-modal-trigger.js';

window.addEventListener('DOMContentLoaded', () => {
  window.customElements.define('vf-modal-trigger', VFModalTrigger);
});
