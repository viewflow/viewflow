/* eslint-env browser */

import {MDCComponent} from '@material/base/component';
import {MDCFloatingLabel} from '@material/floating-label/component';
import {MDCLineRipple} from '@material/line-ripple/component';
import * as menuSurfaceConstants from '@material/menu-surface/constants';
import {MDCMenu} from '@material/menu/component';
import * as menuConstants from '@material/menu/constants';
import {MDCNotchedOutline} from '@material/notched-outline/component';
import {MDCRipple} from '@material/ripple/component';
import {MDCRippleFoundation} from '@material/ripple/foundation';
import {cssClasses, strings, MDCSelectHelperText, MDCSelectIcon} from '@material/select';
import {MDCSelectFoundation} from './foundation';


export class MDCSelect extends MDCComponent {
  static attachTo(root) {
    return new MDCSelect(root);
  }

  initialize(
      labelFactory = (el) => new MDCFloatingLabel(el),
      lineRippleFactory = (el) => new MDCLineRipple(el),
      outlineFactory = (el) => new MDCNotchedOutline(el),
      menuFactory = (el) => new MDCMenu(el),
      iconFactory = (el) => new MDCSelectIcon(el),
      helperTextFactory = (el) => new MDCSelectHelperText(el),
  ) {
    this.selectAnchor =
        this.root.querySelector(strings.SELECT_ANCHOR_SELECTOR);
    this.selectedText =
        this.root.querySelector(strings.SELECTED_TEXT_SELECTOR);
    this.hiddenInput = this.root.querySelector(strings.HIDDEN_INPUT_SELECTOR);

    if (!this.selectedText) {
      throw new Error(
          'MDCSelect: Missing required element: The following selector must be present: ' +
          `'${strings.SELECTED_TEXT_SELECTOR}'`,
      );
    }

    if (this.selectAnchor.hasAttribute(strings.ARIA_CONTROLS)) {
      const helperTextElement = document.getElementById(
          this.selectAnchor.getAttribute(strings.ARIA_CONTROLS));
      if (helperTextElement) {
        this.helperText = helperTextFactory(helperTextElement);
      }
    }

    this.menuSetup(menuFactory);

    const labelElement = this.root.querySelector(strings.LABEL_SELECTOR);
    this.label = labelElement ? labelFactory(labelElement) : null;

    const lineRippleElement =
        this.root.querySelector(strings.LINE_RIPPLE_SELECTOR);
    this.lineRipple =
        lineRippleElement ? lineRippleFactory(lineRippleElement) : null;

    const outlineElement = this.root.querySelector(strings.OUTLINE_SELECTOR);
    this.outline = outlineElement ? outlineFactory(outlineElement) : null;

    const leadingIcon = this.root.querySelector(strings.LEADING_ICON_SELECTOR);
    if (leadingIcon) {
      this.leadingIcon = iconFactory(leadingIcon);
    }

    if (!this.root.classList.contains(cssClasses.OUTLINED)) {
      this.ripple = this.createRipple();
    }
  }

  /**
   * Initializes the select event listeners and internal state based
   * on the environment's state.
   */
  initialSyncWithDOM() {
    this.handleFocus = () => {
      this.foundation.handleFocus();
    };
    this.handleBlur = () => {
      this.foundation.handleBlur();
    };
    this.handleClick = (evt) => {
      this.selectAnchor.focus();
      this.foundation.handleClick(this.getNormalizedXCoordinate(evt));
    };
    this.handleKeydown = (evt) => {
      this.foundation.handleKeydown(evt);
    };
    this.handleMenuItemAction = (evt) => {
      this.foundation.handleMenuItemAction(evt.detail.index);
    };
    this.handleMenuOpened = () => {
      this.foundation.handleMenuOpened();
    };
    this.handleMenuClosed = () => {
      this.foundation.handleMenuClosed();
    };

    this.selectAnchor.addEventListener('focus', this.handleFocus);
    this.selectAnchor.addEventListener('blur', this.handleBlur);

    this.selectAnchor.addEventListener(
        'click', this.handleClick);

    this.selectAnchor.addEventListener('keydown', this.handleKeydown);
    this.menu.listen(
        menuSurfaceConstants.strings.CLOSED_EVENT, this.handleMenuClosed);
    this.menu.listen(
        menuSurfaceConstants.strings.OPENED_EVENT, this.handleMenuOpened);
    this.menu.listen(
        menuConstants.strings.SELECTED_EVENT, this.handleMenuItemAction);

    if (this.hiddenInput) {
      if (this.hiddenInput.value) {
        // If the hidden input already has a value, use it to restore the
        // select value. This can happen e.g. if the user goes back or (in
        // some browsers) refreshes the page.
        this.foundation.setValue(
            this.hiddenInput.value, /** skipNotify */ true);
        this.foundation.layout();
        return;
      }

      this.hiddenInput.value = this.value;
    }
  }

  destroy() {
    this.selectAnchor.removeEventListener('focus', this.handleFocus);
    this.selectAnchor.removeEventListener('blur', this.handleBlur);
    this.selectAnchor.removeEventListener('keydown', this.handleKeydown);
    this.selectAnchor.removeEventListener(
        'click', this.handleClick);

    this.menu.unlisten(
        menuSurfaceConstants.strings.CLOSED_EVENT, this.handleMenuClosed);
    this.menu.unlisten(
        menuSurfaceConstants.strings.OPENED_EVENT, this.handleMenuOpened);
    this.menu.unlisten(
        menuConstants.strings.SELECTED_EVENT, this.handleMenuItemAction);
    this.menu.destroy();

    if (this.ripple) {
      this.ripple.destroy();
    }
    if (this.outline) {
      this.outline.destroy();
    }
    if (this.leadingIcon) {
      this.leadingIcon.destroy();
    }
    if (this.helperText) {
      this.helperText.destroy();
    }

    super.destroy();
  }

  get value() {
    return this.foundation.getValue();
  }

  set value(value) {
    this.foundation.setValue(value);
  }

  get selectedIndex() {
    return this.foundation.getSelectedIndex();
  }

  set selectedIndex(selectedIndex) {
    this.foundation.setSelectedIndex(selectedIndex, /** closeMenu */ false);
  }

  get disabled() {
    return this.foundation.getDisabled();
  }

  set disabled(disabled) {
    this.foundation.setDisabled(disabled);
    if (this.hiddenInput) {
      this.hiddenInput.disabled = disabled;
    }
  }

  set leadingIconAriaLabel(label) {
    this.foundation.setLeadingIconAriaLabel(label);
  }

  set leadingIconContent(content) {
    this.foundation.setLeadingIconContent(content);
  }

  set helperTextContent(content) {
    this.foundation.setHelperTextContent(content);
  }

  set useDefaultValidation(useDefaultValidation) {
    this.foundation.setUseDefaultValidation(useDefaultValidation);
  }

  set valid(isValid) {
    this.foundation.setValid(isValid);
  }

  get valid() {
    return this.foundation.isValid();
  }

  set required(isRequired) {
    this.foundation.setRequired(isRequired);
  }

  get required() {
    return this.foundation.getRequired();
  }

  layout() {
    this.foundation.layout();
  }

  layoutOptions() {
    this.foundation.layoutOptions();
    this.menu.layout();
    // Update cached menuItemValues for adapter.
    this.menuItemValues =
        this.menu.items.map((el) => el.getAttribute(strings.VALUE_ATTR) || '');

    if (this.hiddenInput) {
      this.hiddenInput.value = this.value;
    }
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

  menuSetup(menuFactory) {
    this.menuElement = this.root.querySelector(strings.MENU_SELECTOR);
    this.menu = menuFactory(this.menuElement);
    this.menu.hasTypeahead = true;
    this.menu.singleSelection = false;
    this.menuItemValues =
        this.menu.items.map((el) => el.getAttribute(strings.VALUE_ATTR) || '');
    this.menu.foundation.handleItemAction = function(listItem) {
      const index = this.adapter.getElementIndex(listItem);
      if (index < 0) {
        return;
      }

      this.adapter.notifySelected({index});

      // Wait for the menu to close before adding/removing classes that affect styles.
      this.closeAnimationEndTimerId_ = setTimeout(() => {
        // Recompute the index in case the menu contents have changed.
        const recomputedIndex = this.adapter.getElementIndex(listItem);
        if (recomputedIndex >= 0 &&
            this.adapter.isSelectableItemAtIndex(recomputedIndex)) {
          this.setSelectedIndex(recomputedIndex);
        }
      }, 75);
    };
  }

  createRipple() {
    const adapter = {
      ...MDCRipple.createAdapter({root: this.selectAnchor}),
      registerInteractionHandler: (evtType, handler) => {
        this.selectAnchor.addEventListener(evtType, handler);
      },
      deregisterInteractionHandler: (evtType, handler) => {
        this.selectAnchor.removeEventListener(evtType, handler);
      },
    };
    return new MDCRipple(this.selectAnchor, new MDCRippleFoundation(adapter));
  }

  getSelectAdapterMethods() {
    return {
      getMenuItemAttr: (menuItem, attr) =>
        menuItem.getAttribute(attr),
      setSelectedText: (text) => {
        this.selectedText.textContent = text;
      },
      isSelectAnchorFocused: () => document.activeElement === this.selectAnchor,
      getSelectAnchorAttr: (attr) =>
        this.selectAnchor.getAttribute(attr),
      setSelectAnchorAttr: (attr, value) => {
        this.selectAnchor.setAttribute(attr, value);
      },
      removeSelectAnchorAttr: (attr) => {
        this.selectAnchor.removeAttribute(attr);
      },
      addMenuClass: (className) => {
        this.menuElement.classList.add(className);
      },
      removeMenuClass: (className) => {
        this.menuElement.classList.remove(className);
      },
      openMenu: () => {
        this.menu.open = true;
      },
      closeMenu: () => {
        this.menu.open = false;
      },
      getAnchorElement: () =>
        this.root.querySelector(strings.SELECT_ANCHOR_SELECTOR),
      setMenuAnchorElement: (anchorEl) => {
        this.menu.setAnchorElement(anchorEl);
      },
      setMenuAnchorCorner: (anchorCorner) => {
        this.menu.setAnchorCorner(anchorCorner);
      },
      setMenuWrapFocus: (wrapFocus) => {
        this.menu.wrapFocus = wrapFocus;
      },
      getSelectedIndex: () => {
        return this.menu.selectedIndex;
      },
      setSelectedIndex: (index) => {
        this.menu.selectedIndex = index;
      },
      addSelectedIndex: (index) => {
        const selected = this.menu.selectedIndex;
        const itemIndex = selected.indexOf(index);
        if (itemIndex === -1) {
          selected.push(index);
        }
        // this.menu.selectedIndex = selected;
      },
      focusMenuItemAtIndex: (index) => {
        this.menu.items[index[0] || 0].focus();
      },
      getMenuItemCount: () => this.menu.items.length,
      // Cache menu item values. layoutOptions() updates this cache.
      getMenuItemValues: () => this.menuItemValues,
      getMenuItemTextAtIndex: (index) =>
        this.menu.getPrimaryTextAtIndex(index),
      isTypeaheadInProgress: () => this.menu.typeaheadInProgress,
      typeaheadMatchItem: (nextChar, startingIndex) =>
        this.menu.typeaheadMatchItem(nextChar, startingIndex),
    };
  }

  getCommonAdapterMethods() {
    return {
      addClass: (className) => {
        this.root.classList.add(className);
      },
      removeClass: (className) => {
        this.root.classList.remove(className);
      },
      hasClass: (className) => this.root.classList.contains(className),
      setRippleCenter: (normalizedX) => {
        this.lineRipple && this.lineRipple.setRippleCenter(normalizedX);
      },
      activateBottomLine: () => {
        this.lineRipple && this.lineRipple.activate();
      },
      deactivateBottomLine: () => {
        this.lineRipple && this.lineRipple.deactivate();
      },
      notifyChange: (value) => {
        const index = this.selectedIndex;
        this.emit(strings.CHANGE_EVENT, {value, index}, true /* shouldBubble  */);

        if (this.hiddenInput) {
          this.hiddenInput.value = value;
        }
      },
    };
  }

  getOutlineAdapterMethods() {
    return {
      hasOutline: () => Boolean(this.outline),
      notchOutline: (labelWidth) => {
        this.outline && this.outline.notch(labelWidth);
      },
      closeOutline: () => {
        this.outline && this.outline.closeNotch();
      },
    };
  }

  getLabelAdapterMethods() {
    return {
      hasLabel: () => !!this.label,
      floatLabel: (shouldFloat) => {
        this.label && this.label.float(shouldFloat);
      },
      getLabelWidth: () => this.label ? this.label.getWidth() : 0,
      setLabelRequired: (isRequired) => {
        this.label && this.label.setRequired(isRequired);
      },
    };
  }

  getNormalizedXCoordinate(evt) {
    const targetClientRect = evt.target.getBoundingClientRect();
    const xCoordinate =
        this.isTouchEvent(evt) ? evt.touches[0].clientX : evt.clientX;
    return xCoordinate - targetClientRect.left;
  }

  isTouchEvent(evt) {
    return Boolean(evt.touches);
  }

  getFoundationMap() {
    return {
      helperText: this.helperText ? this.helperText.foundationForSelect :
                                    undefined,
      leadingIcon: this.leadingIcon ? this.leadingIcon.foundationForSelect :
                                      undefined,
    };
  }
}
