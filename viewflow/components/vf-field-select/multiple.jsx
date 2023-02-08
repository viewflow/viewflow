/* eslint-env browser */

import {onCleanup, createEffect} from 'solid-js';
import {customElement} from 'solid-element';
import {select, list} from 'material-components-web';
import cc from 'classcat';

import './index.scss';


class MDCSelectFoundation extends select.MDCSelectFoundation {
  layoutOptions() {
    // do nothing to avoid initial value clear
  }

  toggleSelectedIndex(index, closeMenu = false, skipNotify = false) {
    let currentSelection = this.adapter.getSelectedIndex();
    if (currentSelection===undefined) {
      currentSelection = [];
    } else if (typeof currentSelection === 'number') {
      currentSelection = [currentSelection];
    }

    if (currentSelection.includes(index)) {
      currentSelection.splice(currentSelection.indexOf(index), 1);
      currentSelection.splice(currentSelection.indexOf(index), 1);
    } else {
      currentSelection.push(index);
    }

    currentSelection.sort();
    this.adapter.setSelectedIndex(currentSelection);

    const selectedItemsText = [];
    for (const idx of currentSelection) {
      selectedItemsText.push(this.adapter.getMenuItemTextAtIndex(idx).trim());
    }

    this.adapter.setSelectedText(selectedItemsText.join(',  '));

    if (!skipNotify && this.lastSelectedIndex !== currentSelection) {
      this.handleChange();
    }
    this.lastSelectedIndex = currentSelection;
  }

  getValue() {
    const index = this.adapter.getSelectedIndex();
    const menuItemValues = this.adapter.getMenuItemValues();

    if (index !== -1) {
      const result = [];
      for (const selected of index) {
        result.push(menuItemValues[selected]);
      }
      return result;
    } else {
      return [];
    }
  }

  handleMenuItemAction(index) {
    this.toggleSelectedIndex(index, /** closeMenu */ false);
  }
}

class MDCSelect extends select.MDCSelect {
  menuSetup(menuFactory) {
    super.menuSetup(menuFactory);
    this.menu.singleSelection = false;
    this.menu.list.initializeListType();
    this.menu.foundation.handleItemAction = function(listItem) {
      const index = this.adapter.getElementIndex(listItem);
      if (index < 0) {
        return;
      }
      this.adapter.notifySelected({index: index});
    };
  }

  getSelectAdapterMethods() {
    const result = super.getSelectAdapterMethods();
    result['getSelectedIndex'] = () => {
      return this.menu.selectedIndex;
    };
    return result;
  }

  getDefaultFoundation() {
    const adapter = {
      ...this.getSelectAdapterMethods(),
      ...this.getCommonAdapterMethods(),
      ...this.getOutlineAdapterMethods(),
      ...this.getLabelAdapterMethods(),
    };
    return new MDCSelectFoundation(adapter, this.getFoundationMap());
  }
}

list.MDCListFoundation.prototype.setSelectedIndex = function(index, options) {
  if (options === void 0) {
    options = {};
  }
  if (!this.isIndexValid(index, false) || index == -1) { // fix to avoid error on empty select multiple
    return;
  }

  if (typeof index === 'number') {
    index = [index];
  }

  if (this.isCheckboxList) {
    this.setCheckboxAtIndex(index, options);
  } else if (this.isRadioList) {
    this.setRadioAtIndex(index, options);
  } else {
    this.setSingleSelectionAtIndex(index, options);
  }
};

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
  'value': undefined,
};

const VSelectMultipleField = customElement('vf-field-select-multiple', defaultProps, (props, {element}) => {
  let control;
  let textControl;
  let mdcSelect;
  const selectedItems = [];

  Object.defineProperty(element, 'renderRoot', {
    value: element,
  });

  createEffect(() => {
    if (selectedItems) {
      textControl.textContent = selectedItems.join(', ');
    }
    setTimeout(() => {
      mdcSelect = new MDCSelect(control);
      mdcSelect.foundation.layout();
    });
  });

  onCleanup(() => {
    if (mdcSelect) {
      mdcSelect.destroy();
    }
  });

  const items = (optgroups) => { // todo checkboxes
    const items = [];

    for (const groupData of props.optgroups) {
      if (!groupData.options.value) {
        continue;
      }
      items.push(
          <li
            class="mdc-list-item mdc-list-item--with-one-line mdc-list-item--with-leading-checkbox"
            aria-selected={ groupData.options.selected.toString() }
            aria-checked={ groupData.options.selected ? 'true': false }
            data-value={ groupData.options.value }
            data-menu-item-skip-restore-focus='true'
            role="checkbox">
            <span class="mdc-list-item__ripple"></span>
            <span class="mdc-list-item__start mdc-deprecated-list-item__graphic">
              <div class="mdc-checkbox">
                <input
                  checked={ groupData.options.selected }
                  class="mdc-checkbox__native-control"
                  disabled={ !!props.disabled }
                  name={ groupData.options.name }
                  type="checkbox"
                  value={ groupData.options.value }
                  { ...groupData.options.attrs }/>
                <div class="mdc-checkbox__background">
                  <svg class="mdc-checkbox__checkmark"
                    viewBox="0 0 24 24">
                    <path class="mdc-checkbox__checkmark-path"
                      fill="none"
                      d="M1.73,12.91 8.1,19.28 22.79,4.59"/>
                  </svg>
                  <div class="mdc-checkbox__mixedmark"></div>
                </div>
              </div>
            </span>
            <label class="mdc-list-item__text mdc-list-item__content" for="demo-list-checkbox-item-1">
              { groupData.options.value ? groupData.options.label : '' }
            </label>
          </li>,
      );
      if (groupData.options.selected && groupData.options.value) {
        selectedItems.push(groupData.options.label);
      }
    }

    return items;
  };

  const labelClasses = cc({
    'mdc-floating-label': true,
    'mdc-floating-label--float-above': props.value !== undefined,
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
          <ul class="mdc-list" role="group" aria-label="Food picker listbox">
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
  VSelectMultipleField,
};
