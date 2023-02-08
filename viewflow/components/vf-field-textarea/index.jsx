import {textField} from 'material-components-web';
import {customElement} from 'solid-element';
import {onCleanup, createEffect} from 'solid-js';
import cc from 'classcat';

import './index.scss';


const defaultProps = {
  'cols': undefined,
  'disabled': false,
  'error': undefined,
  'helpText': undefined,
  'id': undefined,
  'label': undefined,
  'name': undefined,
  'required': false,
  'rows': undefined,
  'value': undefined,
};


const VTextareaField = customElement('vf-field-textarea', defaultProps, (props, {element}) => {
  let control;
  let textfield;

  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  createEffect(() => {
    textfield = new textField.MDCTextField(control);
  });

  onCleanup(() => {
    if (textfield) {
      textfield.destroy();
    }
  });

  return (
    <div class="vf-field__row">
      <label
        class={ cc({
          'mdc-text-field': true,
          'mdc-text-field--outlined': true,
          'mdc-text-field--textarea': true,
          'mdc-text-field--invalid': !! props.error,
        }) }
        ref={control}>
        <span class="mdc-notched-outline">
          <span class="mdc-notched-outline__leading"></span>
          <span class="mdc-notched-outline__notch">
            <span class="mdc-floating-label">{ props.label }</span>
          </span>
          <span class="mdc-notched-outline__trailing"></span>
        </span>
        <span class="mdc-text-field__resizer">
          <textarea
            class="mdc-text-field__input"
            cols={ props.cols }
            disabled={ !!props.disabled }
            id={ props.id + '_control' }
            name={ props.name }
            required={ !!props.required }
            rows={ props.rows }
            aria-label={ props.label }>{ props.value }</textarea>
        </span>
      </label>
      { props.helpText || props.error ?
        <div class="mdc-text-field-helper-line">
          <div class="mdc-text-field-helper-text mdc-text-field-helper-text--persistent">
            { props.error || props.helpText }
          </div>
        </div> : '' }
    </div>
  );
});


export {
  VTextareaField,
};
