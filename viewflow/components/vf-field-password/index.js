/* eslint-env browser */

import {customElement} from 'solid-element';
import {createState} from 'solid-js';
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
  'value': undefined,
};

const VPasswordField = customElement('vf-field-password', defaultProps, (props, {element}) => {
  const [state, setState] = createState({
    'visible': props.type !== 'password',
  });

  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  const onBtnClick = (event) => {
    event.preventDefault();
    setState({'visible': !state.visible});
  };

  const inputType = () => state.visible ? 'text': 'password';

  return (
    <div class="vf-field__row">
      <Input
        {...props}
        type={inputType()}
        trailingButton={() => state.visible ? 'visibility' : 'visibility_off'}
        onTrailingButtonClick={onBtnClick}/>
      { props.helpText || props.error ? <HelpText {...props}/> : '' }
    </div>
  );
});

export default VPasswordField;
