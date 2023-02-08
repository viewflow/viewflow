import {onCleanup, createEffect} from 'solid-js';
import {customElement} from 'solid-element';
import {MDCCheckbox} from '@material/checkbox';
import cc from 'classcat';

import './index.scss';


const defaultProps = {
  'checked': undefined,
  'disabled': false,
  'error': undefined,
  'helpText': undefined,
  'id': undefined,
  'label': undefined,
  'name': undefined,
  'required': false,
};


const VCheckboxField = customElement('vf-field-checkbox', defaultProps, (props, {element}) => {
  let control;
  let checkbox;

  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  createEffect(() => {
    checkbox = new MDCCheckbox(control);
  });

  onCleanup(() => {
    if(checkbox) {
      checkbox.destroy();
    }
  });

  return (
    <div class="vf-field__row">
      <div class='vf-field__checkbox-container'>
        <div class="mdc-touch-target-wrapper">
          <div class="vf-field__control mdc-form-field">
            <div
              class={
                cc({
                  'mdc-checkbox': true,
                  'mdc-checkbox--disabled': !!props.disabled,
                })
              }
              ref={control}>
              <input type="checkbox"
                class="mdc-checkbox__native-control"
                checked={ props.checked }
                disabled={ !!props.disabled }
                id={ props.id + '_control' }
                name={ props.name }
                required={ !!props.required }/>
              <div class="mdc-checkbox__background">
                <svg class="mdc-checkbox__checkmark"
                  viewBox="0 0 24 24">
                  <path class="mdc-checkbox__checkmark-path"
                    fill="none"
                    d="M1.73,12.91 8.1,19.28 22.79,4.59"/>
                </svg>
                <div class="mdc-checkbox__mixedmark"></div>
              </div>
              <div class="mdc-checkbox__ripple"></div>
            </div>
            <label for={ props.id + '_control' }>{ props.label }</label>
          </div>
        </div>
        { props.helpText || props.error ?
        <div class="mdc-text-field-helper-line">
          <div class="mdc-text-field-helper-text mdc-text-field-helper-text--persistent">
            { props.error || props.helpText }
          </div>
        </div> : '' }
      </div>
    </div>
  );
});

export {
  VCheckboxField,
};
