/* eslint-env browser */

import {customElement} from 'solid-element';
import {createState} from 'solid-js';
import {noShadowDOM} from 'component-register';
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

  noShadowDOM(element);

  const onBtnClick = (event) => {
    event.preventDefault();
    setState({'visible': !state.visible});
  };

  return (
    <div class="vf-field__row">
      <Input
        {...props}
        type={() => state.visible ? 'text': 'password'}
        trailingButton={() => state.visible ? 'visibility' : 'visibility_off'}
        onTrailingButtonClick={onBtnClick}/>
      { props.helpText || props.error ? <HelpText {...props}/> : '' }
    </div>
  );
});

export default VPasswordField;
