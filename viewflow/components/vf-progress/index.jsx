/* eslint-env browser */

import {customElement} from 'solid-element';
import {onCleanup, createEffect} from 'solid-js';
import {linearProgress} from 'material-components-web';


const VLinearProgress = customElement('vf-linear-progress', {}, (props, {element}) => {
  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  let control;
  let progress;

  createEffect(() => {
    setTimeout(() => {
      progress = new linearProgress.MDCLinearProgress(control);
    });
  });

  onCleanup(() => {
    if (progress) {
      progress.destroy();
    }
  });

  return (
    <div role="progressbar" class="mdc-linear-progress mdc-linear-progress--indeterminate" ref={control}>
      <div class="mdc-linear-progress__buffer">
        <div class="mdc-linear-progress__buffer-bar"></div>
        <div class="mdc-linear-progress__buffer-dots"></div>
      </div>
      <div class="mdc-linear-progress__bar mdc-linear-progress__primary-bar">
        <span class="mdc-linear-progress__bar-inner"></span>
      </div>
      <div class="mdc-linear-progress__bar mdc-linear-progress__secondary-bar">
        <span class="mdc-linear-progress__bar-inner"></span>
      </div>
    </div>
  );
});

export {
  VLinearProgress,
};

