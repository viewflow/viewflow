import {MDCFoundation} from '@material/base/foundation';
import {KEY, normalizeKey} from '@material/dom/keyboard';
import {Corner} from '@material/menu-surface/constants';

import {cssClasses, numbers, strings} from '@material/select';


export class MDCSelectFoundation extends MDCFoundation {
  static get cssClasses() {
    return cssClasses;
  }

  static get defaultAdapter() {
    return {};
  }

  constructor(adapter, foundationMap = {}) {
    super({...MDCSelectFoundation.defaultAdapter, ...adapter});

    this.disabled = false;
    this.isMenuOpen = false;
    this.useDefaultValidation = true;
    this.customValidity = true;
    this.lastSelectedIndex = numbers.UNSET_INDEX;
    this.leadingIcon = foundationMap.leadingIcon;
    this.helperText = foundationMap.helperText;
  }

  getSelectedIndex() {
    return this.adapter.getSelectedIndex();
  }

  addSelectedIndex(index, closeMenu = false, skipNotify = false) {
    const selected = this.adapter.getSelectedIndex().sort();
    const items = [];
    for (const idx of selected) {
      items.push(this.adapter.getMenuItemTextAtIndex(idx).trim());
    }

    this.adapter.setSelectedText(items.join(',  '));

    // this.adapter.addSelectedIndex(index);

    if (!skipNotify && this.lastSelectedIndex !== index) {
      this.handleChange();
    }
    this.lastSelectedIndex = index;
  }


  setSelectedIndex(index, closeMenu = false, skipNotify = false) {
    if (index === []) {
      this.adapter.setSelectedText('');
    } else {
      this.adapter.setSelectedText(
          this.adapter.getMenuItemTextAtIndex(index).trim());
    }

    this.adapter.setSelectedIndex(index);

    if (!skipNotify && this.lastSelectedIndex !== index) {
      this.handleChange();
    }
    this.lastSelectedIndex = index;
  }

  setValue(value, skipNotify = false) {
    const index = this.adapter.getMenuItemValues().indexOf(value);
    this.setSelectedIndex(index, /** closeMenu */ false, skipNotify);
  }

  getValue() {
    const index = this.adapter.getSelectedIndex();
    const menuItemValues = this.adapter.getMenuItemValues();

    if (index !== numbers.UNSET_INDEX) {
      const result = [];
      for (const selected of index) {
        result.push(menuItemValues[selected]);
      }
      return result;
    } else {
      return [];
    }
  }

  getDisabled() {
    return this.disabled;
  }

  setDisabled(isDisabled) {
    this.disabled = isDisabled;
    if (this.disabled) {
      this.adapter.addClass(cssClasses.DISABLED);
      this.adapter.closeMenu();
    } else {
      this.adapter.removeClass(cssClasses.DISABLED);
    }

    if (this.leadingIcon) {
      this.leadingIcon.setDisabled(this.disabled);
    }

    if (this.disabled) {
      // Prevent click events from focusing select. Simply pointer-events: none
      // is not enough since screenreader clicks may bypass this.
      this.adapter.removeSelectAnchorAttr('tabindex');
    } else {
      this.adapter.setSelectAnchorAttr('tabindex', '0');
    }

    this.adapter.setSelectAnchorAttr('aria-disabled', this.disabled.toString());
  }

  /** Opens the menu. */
  openMenu() {
    this.adapter.addClass(cssClasses.ACTIVATED);
    this.adapter.openMenu();
    this.isMenuOpen = true;
    this.adapter.setSelectAnchorAttr('aria-expanded', 'true');
  }

  setHelperTextContent(content) {
    if (this.helperText) {
      this.helperText.setContent(content);
    }
  }

  /**
   * Re-calculates if the notched outline should be notched and if the label
   * should float.
   */
  layout() {
    if (this.adapter.hasLabel()) {
      const optionHasValue = this.getValue().length > 0;
      const isFocused = this.adapter.hasClass(cssClasses.FOCUSED);
      const shouldFloatAndNotch = optionHasValue || isFocused;
      const isRequired = this.adapter.hasClass(cssClasses.REQUIRED);

      this.notchOutline(shouldFloatAndNotch);
      this.adapter.floatLabel(shouldFloatAndNotch);
      this.adapter.setLabelRequired(isRequired);
    }
  }

  /**
   * Synchronizes the list of options with the state of the foundation. Call
   * this whenever menu options are dynamically updated.
   */
  layoutOptions() {
    // const menuItemValues = this.adapter.getMenuItemValues();
    // const selectedIndex = menuItemValues.indexOf(this.getValue());
    // this.setSelectedIndex(selectedIndex, /** closeMenu */ false, /** skipNotify */ true);
  }

  handleMenuOpened() {
    if (this.adapter.getMenuItemValues().length === 0) {
      return;
    }

    // Menu should open to the last selected element, should open to first menu item otherwise.
    const selectedIndex = this.getSelectedIndex();
    const focusItemIndex = selectedIndex >= 0 ? selectedIndex : 0;
    this.adapter.focusMenuItemAtIndex(focusItemIndex);
  }

  handleMenuClosed() {
    this.adapter.removeClass(cssClasses.ACTIVATED);
    this.isMenuOpen = false;
    this.adapter.setSelectAnchorAttr('aria-expanded', 'false');

    // Un focus the select if menu is closed without a selection
    if (!this.adapter.isSelectAnchorFocused()) {
      this.blur();
    }
  }

  /**
   * Handles value changes, via change event or programmatic updates.
   */
  handleChange() {
    this.layout();
    this.adapter.notifyChange(this.getValue());

    const isRequired = this.adapter.hasClass(cssClasses.REQUIRED);
    if (isRequired && this.useDefaultValidation) {
      this.setValid(this.isValid());
    }
  }

  handleMenuItemAction(index) {
    this.addSelectedIndex(index, /** closeMenu */ false);
  }

  /**
   * Handles focus events from select element.
   */
  handleFocus() {
    this.adapter.addClass(cssClasses.FOCUSED);
    this.layout();

    this.adapter.activateBottomLine();
  }

  /**
   * Handles blur events from select element.
   */
  handleBlur() {
    if (this.isMenuOpen) {
      return;
    }
    this.blur();
  }

  handleClick(normalizedX) {
    if (this.disabled) {
      return;
    }

    if (this.isMenuOpen) {
      this.adapter.closeMenu();
      return;
    }

    this.adapter.setRippleCenter(normalizedX);

    this.openMenu();
  }

  handleKeydown(event) {
    if (this.isMenuOpen || !this.adapter.hasClass(cssClasses.FOCUSED)) {
      return;
    }

    const isEnter = normalizeKey(event) === KEY.ENTER;
    const isSpace = normalizeKey(event) === KEY.SPACEBAR;
    const arrowUp = normalizeKey(event) === KEY.ARROW_UP;
    const arrowDown = normalizeKey(event) === KEY.ARROW_DOWN;

    // Typeahead
    if (!isSpace && event.key && event.key.length === 1 ||
        isSpace && this.adapter.isTypeaheadInProgress()) {
      const key = isSpace ? ' ' : event.key;
      const typeaheadNextIndex =
          this.adapter.typeaheadMatchItem(key, this.getSelectedIndex());
      if (typeaheadNextIndex >= 0) {
        this.setSelectedIndex(typeaheadNextIndex);
      }
      event.preventDefault();
      return;
    }

    if (!isEnter && !isSpace && !arrowUp && !arrowDown) {
      return;
    }

    // Increment/decrement index as necessary and open menu.
    if (arrowUp && this.getSelectedIndex() > 0) {
      this.setSelectedIndex(this.getSelectedIndex() - 1);
    } else if (
      arrowDown &&
        this.getSelectedIndex() < this.adapter.getMenuItemCount() - 1) {
      this.setSelectedIndex(this.getSelectedIndex() + 1);
    }

    this.openMenu();
    event.preventDefault();
  }

  notchOutline(openNotch) {
    if (!this.adapter.hasOutline()) {
      return;
    }
    const isFocused = this.adapter.hasClass(cssClasses.FOCUSED);

    if (openNotch) {
      const labelScale = numbers.LABEL_SCALE;
      const labelWidth = this.adapter.getLabelWidth() * labelScale;
      this.adapter.notchOutline(labelWidth);
    } else if (!isFocused) {
      this.adapter.closeOutline();
    }
  }

  setLeadingIconAriaLabel(label) {
    if (this.leadingIcon) {
      this.leadingIcon.setAriaLabel(label);
    }
  }

  setLeadingIconContent(content) {
    if (this.leadingIcon) {
      this.leadingIcon.setContent(content);
    }
  }

  setUseDefaultValidation(useDefaultValidation) {
    this.useDefaultValidation = useDefaultValidation;
  }

  setValid(isValid) {
    if (!this.useDefaultValidation) {
      this.customValidity = isValid;
    }

    this.adapter.setSelectAnchorAttr('aria-invalid', (!isValid).toString());
    if (isValid) {
      this.adapter.removeClass(cssClasses.INVALID);
      this.adapter.removeMenuClass(cssClasses.MENU_INVALID);
    } else {
      this.adapter.addClass(cssClasses.INVALID);
      this.adapter.addMenuClass(cssClasses.MENU_INVALID);
    }

    this.syncHelperTextValidity(isValid);
  }

  isValid() {
    if (this.useDefaultValidation &&
        this.adapter.hasClass(cssClasses.REQUIRED) &&
        !this.adapter.hasClass(cssClasses.DISABLED)) {
      // See notes for required attribute under https://www.w3.org/TR/html52/sec-forms.html#the-select-element
      // TL;DR: Invalid if no index is selected, or if the first index is selected and has an empty value.
      return this.getSelectedIndex() !== numbers.UNSET_INDEX &&
          (this.getSelectedIndex() !== 0 || Boolean(this.getValue()));
    }
    return this.customValidity;
  }

  setRequired(isRequired) {
    if (isRequired) {
      this.adapter.addClass(cssClasses.REQUIRED);
    } else {
      this.adapter.removeClass(cssClasses.REQUIRED);
    }
    this.adapter.setSelectAnchorAttr('aria-required', isRequired.toString());
    this.adapter.setLabelRequired(isRequired);
  }

  getRequired() {
    return this.adapter.getSelectAnchorAttr('aria-required') === 'true';
  }

  init() {
    const anchorEl = this.adapter.getAnchorElement();
    if (anchorEl) {
      this.adapter.setMenuAnchorElement(anchorEl);
      this.adapter.setMenuAnchorCorner(Corner.BOTTOM_START);
    }
    this.adapter.setMenuWrapFocus(false);

    this.setDisabled(this.adapter.hasClass(cssClasses.DISABLED));
    this.syncHelperTextValidity(!this.adapter.hasClass(cssClasses.INVALID));
    this.layout();
    this.layoutOptions();
  }

  /**
   * Un focuses the select component.
   */
  blur() {
    this.adapter.removeClass(cssClasses.FOCUSED);
    this.layout();
    this.adapter.deactivateBottomLine();

    const isRequired = this.adapter.hasClass(cssClasses.REQUIRED);
    if (isRequired && this.useDefaultValidation) {
      this.setValid(this.isValid());
    }
  }

  syncHelperTextValidity(isValid) {
    if (!this.helperText) {
      return;
    }

    this.helperText.setValidity(isValid);

    const helperTextVisible = this.helperText.isVisible();
    const helperTextId = this.helperText.getId();

    if (helperTextVisible && helperTextId) {
      this.adapter.setSelectAnchorAttr(strings.ARIA_DESCRIBEDBY, helperTextId);
    } else {
      // Needed because screenreaders will read labels pointed to by
      // `aria-describedby` even if they are `aria-hidden`.
      this.adapter.removeSelectAnchorAttr(strings.ARIA_DESCRIBEDBY);
    }
  }
}

export default MDCSelectFoundation;
