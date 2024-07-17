/* eslint-env browser */

import {customElement} from 'solid-element';
import {textField} from 'material-components-web';
import {onCleanup, createEffect} from 'solid-js';
import cc from 'classcat';

import './index.scss';

export const defaultProps = {
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
  'value': '',
  'readonly': undefined,
  'pattern': undefined,
};

const HelpText = (props) => {
  return (
    <div class="mdc-text-field-helper-line">
      <div class="mdc-text-field-helper-text mdc-text-field-helper-text--persistent">
        { props.error || props.helpText }
      </div>
    </div>
  );
};

const Input = (props) => {
  let control;
  let textfield;

  createEffect(() => {
    setTimeout(() => {
      textfield = new textField.MDCTextField(control);
      control.textfield=textfield;
    });
  });

  createEffect(() => {
    props.value;
    if (textfield) {
      textfield.layout();
    }
  });

  onCleanup(() => {
    if (textfield) {
      textfield.destroy();
    }
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
            'mdc-floating-label--float-above': Boolean(props.value),
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
        tabindex={ props.tabIndex }
        value={ props.value }
        readonly= {props.readonly }
        pattern= {props.pattern}
        aria-labelledby={ props.id + '_label' }
        oninput={props.onInput}
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
  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  return (
    <div class="vf-field__row">
      <Input {...props}/>
      { props.helpText || props.error ? <HelpText {...props}/> : '' }
    </div>
  );
});

export {
  HelpText,
  Input,
  VInputField,
};
