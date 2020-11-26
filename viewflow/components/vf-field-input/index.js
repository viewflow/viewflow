/* eslint-env browser */

import {customElement} from 'solid-element';
import {MDCTextField} from '@material/textfield';
import {noShadowDOM} from 'component-register';
import {onCleanup, afterEffects} from 'solid-js';
import cc from 'classcat';

import './index.scss';

const defaultProps = {
  'autofocus': undefined,
  'disabled': false,
  'error': undefined,
  'helpText': undefined,
  'id': undefined,
  'label': undefined,
  'leadingIcon': undefined,
  'maxlength': undefined,
  'minlength': undefined,
  'name': undefined,
  'placeholder': undefined,
  'required': false,
  'step': undefined,
  'trailingIcon': undefined,
  'type': 'text',
  'value': undefined,
};

export const HelpText = (props) => {
  return (
    <div class="mdc-text-field-helper-line">
      <div class="mdc-text-field-helper-text mdc-text-field-helper-text--persistent">
        { props.error || props.helpText }
      </div>
    </div>
  );
};

export const Input = (props) => {
  let control;
  let textfield;

  afterEffects(() => {
    setTimeout(() => {
      textfield = new MDCTextField(control);
      control.textfield=textfield;
    });
  });

  onCleanup(() => {
    textfield.destroy();
  });

  return (
    <label
      class={ cc({
        'mdc-text-field': true,
        'mdc-text-field--outlined': true,
        'mdc-text-field--invalid': !! props.error,
        'mdc-text-field--with-leading-icon': !!props.leadingIcon,
        'mdc-text-field--with-trailing-icon': !!props.trailingIcon,
      }) }
      ref={control}>
      <span class="mdc-notched-outline">
        <span class="mdc-notched-outline__leading"></span>
        <span class="mdc-notched-outline__notch">
          { props.label ? <span class={cc({
            'mdc-floating-label': true,
            'mdc-floating-label--float-above': props.value !== undefined,
            'mdc-floating-label--required': props.required,
          })} id={ props.id +'_label' }>{ props.label }</span> : '' }
        </span>
        <span class="mdc-notched-outline__trailing"></span>
      </span>
      { props.leadingIcon ?
        <i class="material-icons mdc-text-field__icon mdc-text-field__icon--leading" tabindex="-1" role="button">
          { props.leadingIcon }
        </i> : '' }
      <input
        autofocus={ !!props.autofocus }
        autocomplete={props.autocomplete}
        class="mdc-text-field__input"
        disabled={ !!props.disabled }
        id={ props.id + '_control' }
        maxlength={ props.maxlength }
        minlength={ props.minlength }
        name={ props.name }
        placeholder={ props.placeholder }
        required={ !!props.required }
        step = { props.step }
        type={ props.type }
        value={ props.value }
        aria-labelledby={ props.id + '_label' }
        onChange={props.onChange}
        onFocus={props.onFocus}
        onKeyUp={props.onKeyUp}
        onKeyDown={props.onKeyDown}/>
      { props.trailingButton ?
        <div class="mdc-touch-target-wrapper">
          <button
            class="mdc-button vf-text-field__button mdc-button--touch"
            onClick={ props.onTrailingButtonClick }
            disabled={ props.disabled }
            type="button">
            <div class="mdc-button__ripple"></div>
            <span class="mdc-button__label material-icons">{ props.trailingButton }</span>
            <div class="mdc-button__touch"></div>
          </button>
        </div> :
        props.trailingIcon ?
          <i class="material-icons mdc-text-field__icon mdc-text-field__icon--trailing" tabindex="-1" role="button">
            { props.trailingIcon }
          </i> : ''
      }
    </label>
  );
};

const VInputField = customElement('vf-field-input', defaultProps, (props, {element}) => {
  noShadowDOM(element);

  return (
    <div class="vf-field__row">
      <Input {...props}/>
      { props.helpText || props.error ? <HelpText {...props}/> : '' }
    </div>
  );
});

export default VInputField;
