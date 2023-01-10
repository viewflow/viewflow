/* eslint-env browser */

import {customElement} from 'solid-element';
import {createSignal} from 'solid-js';
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
  'maxlength': undefined,
  'minlength': undefined,
  'name': undefined,
  'placeholder': undefined,
  'required': false,
  'type': 'password',
  'value': '',
};

const VPasswordField = customElement('vf-field-password', defaultProps, (props, {element}) => {
  const [visible, setVisible] = createSignal(props.type !== 'password');

  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  const onBtnClick = (event) => {
    event.preventDefault();
    setVisible(!visible());
  };

  const inputType = () => visible() ? 'text': 'password';

  return (
    <div class="vf-field__row">
      <Input
        {...props}
        type={inputType()}
        trailingButton={() => visible() ? 'visibility' : 'visibility_off'}
        onTrailingButtonClick={onBtnClick}/>
      { props.helpText || props.error ? <HelpText {...props}/> : '' }
    </div>
  );
});


export {
  VPasswordField,
};
