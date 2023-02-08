/* eslint-env browser */

import {customElement} from 'solid-element';
import {createSignal, onCleanup, createEffect} from 'solid-js';
import {MDCDialog} from '@material/dialog';

import {Input, HelpText} from '../vf-field-input';
import Calendar from './calendar';
import './index.scss';

const defaultProps = {
  'autofocus': undefined,
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


const VDateField = customElement('vf-field-date', defaultProps, (props, {element}) => {
  let dialog;
  let dialogEl;

  const [getState, setState] = createSignal({
    'selected': props.value,
    'current': undefined,
    'isOpen': false,
  });

  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });


  createEffect(() => {
    setTimeout(() => {
      dialog = new MDCDialog(dialogEl);
    });
  });

  onCleanup(() => {
    if(dialog) {
      dialog.destroy();
    }
  });


  const onDateChange = (value) => {
    setState((state) => { return {...state, current: value}});
  };

  const onBtnClick = () => {
    setState((state) => { return {...state, isOpen: true, current: undefined}});
    dialog.open();
    dialog.listen('MDCDialog:closing', function(event) {
      setState((state) => {
        return {
          ...state,
          isOpen: false,
          selected: event.detail.action == 'accept' ? getState().current || getState().selected : getState().selected,
        }
      });
      element.querySelector('.mdc-text-field').textfield.layout();
    });
  };

  const onInputChange = (event) => {
    setState((state) => { return {...state, selected: event.target.value}});
    props.value = event.target.value;
  };

  return (
    <div class="vf-field__row">
      <Input
        {...props}
        onChange={onInputChange}
        value={getState().selected}
        trailingButton='today'
        onTrailingButtonClick={onBtnClick}/>
      { props.helpText || props.error ? <HelpText {...props}/> : '' }
      <aside class='mdc-dialog' ref={dialogEl}>
        <div class="mdc-dialog__container">
          <div class='mdc-dialog__surface vf-datepicker__surface'>
            <div class='mdc-dialog__content'>
              {getState().isOpen ? <Calendar
                {...props}
                value = { getState().selected || '' }
                header={ true }
                actions={ true }
                onChange={onDateChange}/> : '' }
            </div>
          </div>
        </div>
        <div class="mdc-dialog__scrim"></div>
      </aside>
    </div>
  );
});

export {
  VDateField
};
