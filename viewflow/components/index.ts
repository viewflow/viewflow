import './index.scss';

import {MDCRipple} from '@material/ripple';
import {MDCCheckbox} from '@material/checkbox';
import {MDCChipSet} from '@material/chips/deprecated';
import {MDCCircularProgress} from '@material/circular-progress';
import {MDCDialog} from '@material/dialog';
import {MDCDrawer} from "@material/drawer";
import {MDCFloatingLabel} from '@material/floating-label';
import {MDCFormField} from '@material/form-field';
import {MDCIconButtonToggle} from '@material/icon-button';
import {MDCLineRipple} from '@material/line-ripple';
import {MDCLinearProgress} from '@material/linear-progress';
import {MDCList} from "@material/list";
import {MDCMenu} from '@material/menu';
import {MDCNotchedOutline} from '@material/notched-outline';
import {MDCRadio} from '@material/radio';
import {MDCSegmentedButton} from '@material/segmented-button';
import {MDCSelect} from '@material/select';
import {MDCSlider} from '@material/slider';
import {MDCSnackbar} from '@material/snackbar';
import {MDCSwitch} from '@material/switch';
import {MDCTabBar} from '@material/tab-bar';
import {MDCTabIndicator} from '@material/tab-indicator';
import {MDCTabScroller} from '@material/tab-scroller';
import {MDCTextField} from '@material/textfield';
import {MDCTooltip} from '@material/tooltip';
import {MDCTopAppBar} from '@material/top-app-bar';

import './vf-field';
import './vf-page-lockscreen';
import './vf-workflow';

import {VCardMenu} from './vf-card';
import {VCheckboxField} from './vf-field-checkbox';
import {VDateField, VInlineCalendarField, VTimeField} from './vf-field-datetime';
import {VFileInputField} from './vf-field-file';
import {VInputField} from './vf-field-input';
import {VPasswordField} from './vf-field-password';
import {VRadioSelectField} from './vf-field-radio-select';
import {VSelectField, VSelectMultipleField} from './vf-field-select';
import {VTextareaField} from './vf-field-textarea';
import {VFormElement} from './vf-form';
import {VListBulkActions, VListFilter, VListFilterTrigger, VListPagination, VList} from './vf-list';
import {VFModalTrigger} from './vf-modal';
import {VPage, VPageMenuToggle, VPageMenuNavigation, VPageScrollFix, VDialog} from './vf-page';
import {VPageProfileAvatar} from './vf-page-profile';
import {VFPageReload} from './vf-page-reload';
import {VPerfectScroll} from './vf-perfect-scroll';
import {VLinearProgress} from './vf-progress';
import {VSnackbar} from './vf-snackbar';
import {VTurbo} from './vf-turbo';

import {VDash} from '../contrib/plotly';


window.addEventListener('DOMContentLoaded', () => {
  window.customElements.define('vf-card-menu', VCardMenu);
  window.customElements.define('vf-dialog', VDialog);
  window.customElements.define('vf-form', VFormElement);
  window.customElements.define('vf-list-bulk-actions', VListBulkActions);
  window.customElements.define('vf-list-filter-trigger', VListFilterTrigger);
  window.customElements.define('vf-list-filter', VListFilter);
  window.customElements.define('vf-list-pagination', VListPagination);
  window.customElements.define('vf-list', VList);
  window.customElements.define('vf-modal-trigger', VFModalTrigger);
  window.customElements.define('vf-page-menu-navigation', VPageMenuNavigation);
  window.customElements.define('vf-page-menu-toggle', VPageMenuToggle);
  window.customElements.define('vf-page-profile-avatar', VPageProfileAvatar);
  window.customElements.define('vf-page-reload', VFPageReload);
  window.customElements.define('vf-page-scroll-fix', VPageScrollFix);
  window.customElements.define('vf-page', VPage);
  window.customElements.define('vf-perfect-scroll', VPerfectScroll);
  window.customElements.define('vf-snackbar', VSnackbar);
  window.customElements.define('vf-turbo', VTurbo);
});

export {
  MDCRipple,
  MDCCheckbox,
  MDCChipSet,
  MDCCircularProgress,
  MDCDialog,
  MDCDrawer,
  MDCFloatingLabel,
  MDCFormField,
  MDCIconButtonToggle,
  MDCLineRipple,
  MDCList,
  MDCLinearProgress,
  MDCMenu,
  MDCNotchedOutline,
  MDCRadio,
  MDCSegmentedButton,
  MDCSelect,
  MDCSlider,
  MDCSnackbar,
  MDCSwitch,
  MDCTabBar,
  MDCTabIndicator,
  MDCTabScroller,
  MDCTextField,
  MDCTooltip,
  MDCTopAppBar,

  VCardMenu,
  VCheckboxField,
  VDateField,
  VInlineCalendarField,
  VTimeField,
  VFileInputField,
  VFormset,
  VInputField,
  VPasswordField,
  VRadioSelectField,
  VSelectField,
  VTextareaField,
  VFormElement,
  VListBulkActions,
  VListFilter,
  VListFilterTrigger,
  VListPagination,
  VList,
  VFModalTrigger,
  VPage,
  VPageMenuToggle,
  VPageMenuNavigation,
  VPageScrollFix,
  VDialog,
  VPageProfileAvatar,
  VFPageReload,
  VPerfectScroll,
  VLinearProgress,
  VSnackbar,
  VTurbo,
  VDash,
};
