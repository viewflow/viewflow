/* eslint-env browser */

import {customElement} from 'solid-element';
import {createSignal} from 'solid-js';
import {onCleanup, createEffect} from 'solid-js';
import {MDCDialog} from '@material/dialog';
import cc from 'classcat';

import {Input, HelpText} from '../vf-field-input';
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

const Time = (props) => {
  // const [state, setState] = createState({
  //   'hour': new Date().getHours(),
  //   'day': new Date().getMinutes(),
  //   'selected': NaN,
  // });

  return (
    <div class={cc({
      'vf-time': true,
      'vf-time--disabled': !!props.disabled,
    })}>
      <div class="vf-time__body">
        <div class='vf-time__surface'>
          <Input/>
          <span>:</span>
          <Input/>
        </div>
        { props.actions ?
          <div class="vf-calendar__actions">
            <button
              type_="button"
              class="mdc-button mdc-dialog__footer__button"
              data-mdc-dialog-action="close">
              <div class="mdc-button__ripple"></div>
              <span class="mdc-button__label">cancel</span>
              <div class="mdc-button__touch"></div>
            </button>
            <button
              type_="button"
              class="mdc-button mdc-dialog__footer__button"
              data-mdc-dialog-action="accept" data-mdc-dialog-button-default data-mdc-dialog-initial-focus>
              <div class="mdc-button__ripple"></div>
              <span class="mdc-button__label">ok</span>
              <div class="mdc-button__touch"></div>
            </button>
          </div> :''}
      </div>
    </div>
  );
};


const VTimeField = customElement('vf-field-time', defaultProps, (props, {element}) => {
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
    if (dialog) {
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
          selected: event.detail.action == 'accept' ? state.current || state.selected : state.selected,
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
        value={ getState().selected }
        trailingIcon={() => 'schedule'}
        onTrailingButtonClick={onBtnClick}/>
      { props.helpText || props.error ? <HelpText {...props}/> : '' }
      <aside class='mdc-dialog' ref={dialogEl}>
        <div class="mdc-dialog__container">
          <div class='mdc-dialog__surface vf-datepicker__surface'>
            <div class='mdc-dialog__content'>
              {getState().isOpen ? <Time
                {...props}
                value = { getState().selected }
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
  VTimeField
};
