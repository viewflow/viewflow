import {customElement} from 'solid-element';
import cc from 'classcat';

import './index.scss';


const defaultProps = {
  'disabled': false,
  'error': undefined,
  'helpText': undefined,
  'id': undefined,
  'inline': undefined,
  'label': undefined,
  'name': undefined,
  'optgroups': undefined,
  'required': false,
  'value': undefined,
};


const VRadioSelectField = customElement('vf-field-radio-select', defaultProps, (props, {element}) => {
  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  const items = (props) => {
    const items = [];

    for (const groupData of props.optgroups) {
      items.push(
          <div class="mdc-form-field">
            <div
              class={
                cc({
                  'mdc-radio': true,
                  'mdc-radio--disabled': !!props.disabled,
                })}>
              <input
                checked={ groupData.options.selected }
                class="mdc-radio__native-control"
                disabled={ !!props.disabled }
                name={ groupData.options.name }
                type="radio"
                value={ groupData.options.value }
                { ...groupData.options.attrs }/>
              <div class="mdc-radio__background">
                <div class="mdc-radio__outer-circle"></div>
                <div class="mdc-radio__inner-circle"></div>
              </div>
              <div class="mdc-radio__ripple"></div>
            </div>
            <label for={ groupData.options.attrs.id }>{ groupData.options.label }</label>
          </div>,
      );
    }
    return items;
  };

  return (
    <div class={
      cc({
        'vf-field__row': true,
        'vf-radio--inline': !!props.inline,
        'vf-radio--invalid': !! props.error,
      })}
    >
      <label class="vf-radio-select__label mdc-floating-label">{ props.label }</label>
      <div class="vf-radio-select__control">
        { items(props) }
      </div>
      { props.helpText || props.error ?
        <div class="mdc-text-field-helper-line">
          <div class="mdc-text-field-helper-text mdc-text-field-helper-text--persistent">
            { props.error || props.helpText }
          </div>
        </div> : '' }
    </div>
  );
});


export {
  VRadioSelectField,
};
