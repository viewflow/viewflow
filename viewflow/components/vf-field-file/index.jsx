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
  'value': '',
  'multiple': undefined,
};

const VFileInputField = customElement('vf-field-file', defaultProps, (props, {element}) => {
  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  const [value, setValue] = createSignal(props.value);

  const onFileChange = (event) => {
    event.preventDefault();

    const files = event.srcElement.files;
    const fileNames = [];
    for (let i = 0; i < files.length; i++) {
      fileNames.push(files[i].name);
    }
    setValue(fileNames.join(', '));
  };

  const onTrailingButtonClick = () => {
    element.querySelector('input[type=file]').click();
  };

  return (
    <div class="vf-field__row" style="position:relative">
      <Input
        disabled={props.disabled}
        id={props.id + '_input'}
        label={props.label}
        required={props.required}
        tabIndex="-1"
        trailingButton="file_upload"
        value={value()}
        onTrailingButtonClick={onTrailingButtonClick}
      />
      { props.helpText || props.error ? <HelpText {...props}/> : '' }
      { !props.disabled ?
        <input
          class="vf-field__file-input"
          multiple={props.multiple}
          type="file"
          {...props}
          value=""
          name={props.name}
          id={props.id}
          required={props.required}
          tabindex="-1"
          onChange={onFileChange}/> :
      '' }
    </div>
  );
});

export {
  VFileInputField,
};
