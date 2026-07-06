/* eslint-env browser */

import {customElement} from 'solid-element';
import {createSignal} from 'solid-js';

import {Input, HelpText} from '../vf-field-input';
import './index.scss';

const defaultProps = {
  'autofocus': false,
  'disabled': false,
  'error': undefined,
  'helpText': undefined,
  'id': undefined,
  'label': undefined,
  'leadingIcon': undefined,
  'name': undefined,
  'placeholder': undefined,
  'required': false,
  'type': 'text',
  'value': '',
  'format': undefined,
};

const VTimeField = customElement('vf-field-time', defaultProps, (props, {element}) => {
  const [getState, setState] = createSignal({
    'selected': props.value,
  });

  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  const onInputChange = (event) => {
    setState((state) => { return {...state, selected: event.target.value}});
    props.value = event.target.value;
  };

  return (
    <div class="vf-field__row">
      <Input
        {...props}
        onChange={onInputChange}
        value={ getState().selected }/>
      { props.helpText || props.error ? <HelpText {...props}/> : '' }
    </div>
  );
});


export {
  VTimeField
};
