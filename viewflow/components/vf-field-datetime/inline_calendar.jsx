/* eslint-env browser */

import {customElement} from 'solid-element';
import {createSignal} from 'solid-js';
import cc from 'classcat';

import Calendar from './calendar';
import './index.scss';


const defaultProps = {
  'autofocus': undefined,
  'disabled': false,
  'error': undefined,
  'helpText': undefined,
  'id': undefined,
  'label': undefined,
  'name': undefined,
  'required': false,
  'type': 'text',
  'value': undefined,
  'format': undefined,
};


const VInlineCalendarField = customElement('vf-field-inline-calendar', defaultProps, (props, {element}) => {
  const [state, setState] = createSignal({
    'selected': props.value,
  });

  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  const onChange = (value) => {
    setState({...state, selected: value});
  };

  return (
    <div class="vf-field__row">
      <label class={cc({
        'vf-inline-calendar__label': true,
        'vf-inline-calendar__label--invalid': !!props.errors,
        'vf-inline-calendar__label--required': !!props.required,
      })}>{ props.label }</label>
      <Calendar header={ false } actions={ false } onChange={ onChange} {...props}/>
      <input
        id={ props.id }
        name={ props.name }
        required={ !!props.required }
        value={ state.selected }
        type="hidden"/>
      { props.helpText || props.error ?
        <p class={ cc({
          'vf-inline-calendar__helptext': true,
          'vf-inline-calendar__helptext--invalid': !!props.errors,
        })}>
          { props.error || props.helpText }
        </p> : '' }
    </div>
  );
});

export {
  VInlineCalendarField,
}

