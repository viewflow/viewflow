/* eslint-env browser */

import {onCleanup, createEffect} from 'solid-js';
import {customElement} from 'solid-element';
import {select} from 'material-components-web';
import cc from 'classcat';

import './index.scss';
import {VSelectMultipleField} from './multiple.jsx';


const defaultProps = {
  'disabled': false,
  'error': undefined,
  'helpText': undefined,
  'id': undefined,
  'label': undefined,
  'leadingIcon': undefined,
  'name': undefined,
  'optgroups': undefined,
  'required': false,
  'trailingIcon': undefined,
  'value': '',
};


const VSelectField = customElement('vf-field-select', defaultProps, (props, {element}) => {
  let control;
  let textControl;
  let input;
  let mdcSelect;

  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  createEffect(() => {
    setTimeout(() => {
      mdcSelect = new select.MDCSelect(control);
      mdcSelect.foundation.layout();

      mdcSelect.listen('MDCSelect:change', () => {
        const event = new CustomEvent('change', {
          bubbles: true,
          detail: {index: mdcSelect.selectedIndex, value: mdcSelect.value},
        });
        element.dispatchEvent(event);
      });
    });
  });

  onCleanup(() => {
    if (mdcSelect) {
      mdcSelect.destroy();
    }
  });

  const items = (optgroups) => {
    let selectedItemText = '';
    const items = [];

    for (const groupData of props.optgroups) {
      items.push(
          <li
            class={'mdc-list-item mdc-list-item--with-one-line' +
              (groupData.options.selected ? ' mdc-list-item--selected': '')}
            aria-selected={ groupData.options.selected.toString() }
            data-value={ groupData.options.value }
            role="option">
            <span class="mdc-list-item__ripple"></span>
            <span class="mdc-list-item__text mdc-list-item__content">
              { groupData.options.value ? groupData.options.label : '' }
            </span>
          </li>,
      );
      if (groupData.options.selected && groupData.options.value) {
        selectedItemText = groupData.options.label;
      }
    }

    textControl.textContent = selectedItemText;
    if (!selectedItemText && mdcSelect) {
      mdcSelect.selectedIndex = -1;
    }
    setTimeout(() => {
      if (mdcSelect) {
        mdcSelect.destroy()
        mdcSelect = new select.MDCSelect(control);
        const event = new CustomEvent('change', {
          bubbles: true,
          detail: {index: -1, value: undefined},
        });
        element.dispatchEvent(event);

        mdcSelect.layoutOptions();
      }
    });
    return items;
  };

  const labelClasses = cc({
    'mdc-floating-label': true,
    'mdc-floating-label--float-above': props.value !== '',
    'mdc-floating-label--required': props.required,
  });

  return (
    <div class="vf-field__row">
      <div
        class={ cc({
          'mdc-select': true,
          'mdc-select--outlined': true,
          'mdc-select--disabled': !!props.disabled,
          'mdc-select--required': !!props.required,
          'mdc-select--invalid': !! props.error,
        }) }
        ref={control}>
        <input
          disabled={ !!props.disabled }
          id={ props.id + '_control' }
          name={ props.name }
          ref={ input }
          type="hidden"
          value={ props.value }/>
        <div
          class="mdc-select__anchor"
          aria-disabled={ !props.disabled ? false : 'true' }
          aria-required={ !props.required ? false : 'true' }
          role="button"
          aria-haspopup="listbox"
          aria-expanded="false"
          aria-labelledby={ props.id +'_label ' + props.id + '_text'}>
          <span class="mdc-notched-outline">
            <span class="mdc-notched-outline__leading"></span>
            <span class="mdc-notched-outline__notch">
              <span class={ labelClasses } id={ props.id +'_label' }>{ props.label }</span>
            </span>
            <span class="mdc-notched-outline__trailing"></span>
          </span>
          <span class="mdc-select__selected-text-container">
            <span id={ props.id +'_text' } class="mdc-select__selected-text" ref={ textControl }></span>
          </span>
          <span class="mdc-select__dropdown-icon">
            <svg
              class="mdc-select__dropdown-icon-graphic"
              viewBox="7 10 10 5" focusable="false">
              <polygon
                class="mdc-select__dropdown-icon-inactive"
                stroke="none"
                fill-rule="evenodd"
                points="7 10 12 15 17 10">
              </polygon>
              <polygon
                class="mdc-select__dropdown-icon-active"
                stroke="none"
                fill-rule="evenodd"
                points="7 15 12 10 17 15">
              </polygon>
            </svg>
          </span>
        </div>

        <div class="mdc-select__menu mdc-menu mdc-menu-surface mdc-menu-surface--fullwidth">
          <ul class="mdc-list" role="listbox" aria-label={ props.label }>
            { items(props.optgroups) }
          </ul>
        </div>
      </div>
      { props.helpText || props.error ?
      <p class="mdc-select-helper-text">
        { props.error || props.helpText }
      </p> : '' }
    </div>
  );
});

export {
  VSelectField,
  VSelectMultipleField,
};
