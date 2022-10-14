/* eslint-env browser */

import {checkbox, select} from 'material-components-web';
import {interpolate, gettext} from '../django-i18n/index';
import {input} from '../vf-field/jhtml';


export class VListBulkActions extends HTMLElement {
  connectedCallback() {
    this._selectedSet = new Set();
    this._allPagesSelected = false;

    this._pagePath = window.location.pathname;
    this._persistentStateVar = `v_list_selected_` + this._pagePath.replace(/\//g, '_');

    this._headerEl = this.parentNode.querySelector('table thead tr');
    this._selectAllEl = this.parentNode.querySelector('.vf-list__action-header .mdc-checkbox');
    this._selectAllMDC= new checkbox.MDCCheckbox(this._selectAllEl);
    this._actionCells = this.parentNode.querySelectorAll('.vf-list__action-cell .mdc-checkbox input');
    this._selectAllBtn = this.parentNode.querySelector('.vf-list__action-select-all');
    this._selectedTextEl = this.parentElement.querySelector('.vf-list__action-selected');
    this._actionFormEl = this.parentElement.querySelector('.vf-list__action-form');
    this._buttonEl = this._actionFormEl.querySelector('button');
    this._mdcSelectField = new select.MDCSelect(this.parentNode.querySelector('.vf-list__action-select .mdc-select'));
    this._mdcSelectField.menu.setFixedPosition(true);

    this._totalCount = parseInt(this.parentNode.querySelector('table').dataset.totalItemsCount) || 0;

    this.parentNode.addEventListener('click', this.onClick);
    this._actionFormEl.addEventListener('submit', this.onSubmit);
    window.addEventListener('turbo:before-render', this.onPageChange);
    window.addEventListener('unload', this.onUnload);

    this.load();
    this.updateState();
  }

  disconnectedCallback() {
    this._selectAllMDC.destroy();
    // TODO: this._mdcSelectField.destroy();

    this.parentNode.removeEventListener('click', this.onClick);
    this._actionFormEl.removeEventListener('submit', this.onSubmit);
    window.removeEventListener('turbo:before-render', this.onPageChange);
    window.removeEventListener('unload', this.onUnload);
  }

  load() {
    const storedValue = window.sessionStorage.getItem(this._persistentStateVar);
    if (storedValue==='all') {
      this._allPagesSelected = true;
    } else {
      try {
        this._selectedSet = new Set(JSON.parse(storedValue || '[]'));
      } catch (e) {
        console.error('Invalid JSON ' + storedValue);
      }
    }
  }

  dump() {
    if (this._allPagesSelected) {
      return 'all';
    } else {
      return JSON.stringify(Array.from(this._selectedSet));
    }
  }

  updateState() {
    // Action header
    this._headerEl.classList.toggle('vf-list__action--active', this._allPagesSelected || this._selectedSet.size);
    this._headerEl.classList.toggle('vf-list-row--selected', this._allPagesSelected);
    this._selectAllBtn.classList.toggle(
        'vf-list__action-select-all--selected',
        !this._totalCount || this._allPagesSelected,
    );

    if (this._totalCount) {
      this._selectedTextEl.textContent = interpolate(
          gettext('%(sel)s of %(cnt)s selected'),
          {
            sel: this._allPagesSelected ? this._totalCount : this._selectedSet.size,
            cnt: this._totalCount,
          }, true);
    } else {
      this._selectedTextEl.textContent = interpolate(
          gettext('%(sel)s selected'),
          {
            sel: this._selectedSet.size,
          }, true);
    }

    // individual checkboxes state
    this._actionCells.forEach((cell) => {
      const rowEl = cell.closest('tr');
      const checked = this._allPagesSelected || this._selectedSet.has(rowEl.dataset.rowId);
      rowEl.classList.toggle('vf-list-row--selected', checked);
      cell.checked = checked;
    });

    // select all checkbox
    if (this._allPagesSelected) {
      this._selectAllMDC.checked = true;
      this._selectAllMDC.indeterminate = false;
    } else if (this._selectedSet.size == 0) {
      this._selectAllMDC.checked = false;
      this._selectAllMDC.indeterminate = false;
    } else {
      const onPageSet = Array.prototype.map.call(
          this._actionCells,
          (elem) => elem.closest('tr').dataset.rowId,
      );
      if (onPageSet.every((val) => this._selectedSet.has(val))) {
        this._selectAllMDC.checked = true;
        this._selectAllMDC.indeterminate = false;
      } else {
        this._selectAllMDC.indeterminate = true;
      }
    }

    // button state
    // TODO: this._buttonEl.disabled = !this._mdcSelectField.value;
  }

  onPageChange = () => {
    if (this._pagePath === window.location.pathname) {
      window.sessionStorage.setItem(this._persistentStateVar, this.dump());
    } else {
      window.sessionStorage.removeItem(this._persistentStateVar);
    }
  }

  onUnload = () => {
    window.sessionStorage.removeItem(this._persistentStateVar);
  }

  onClick = (event) => {
    if (event.srcElement.parentNode == this._selectAllBtn) {
      this._allPagesSelected = true;
      this.updateState();
    } else if (event.srcElement.type == 'checkbox') {
      if (event.srcElement.closest('.vf-list__action-header')) {
        // select all checkbox
        if (this._allPagesSelected) {
          this._allPagesSelected = false;
          this._selectedSet = new Set();
        } else {
          this._actionCells.forEach((cell) => {
            const rowEl = cell.closest('tr');
            if (event.srcElement.checked) {
              this._selectedSet.add(rowEl.dataset.rowId);
            }
          });
          if (!event.srcElement.checked) {
            this._selectedSet.clear();
          }
        }
        this.updateState();
      } else {
        const rowEl = event.srcElement.closest('[data-row-id]');
        if (rowEl) {
          // select a row checkbox
          const checkboxEl = rowEl.querySelector('.vf-list__action-cell .mdc-checkbox input');
          if (checkboxEl.checked) {
            this._selectedSet.add(rowEl.dataset.rowId);
          } else {
            this._selectedSet.delete(rowEl.dataset.rowId);
            this._allPagesSelected = false;
          }
          this.updateState();
        }
      }
    }
  }

  onSubmit = () => {
    this._actionFormEl.action = this._mdcSelectField.value;
    window.history.pushState({}, document.title, this._mdcSelectField.value);
    if (this._allPagesSelected) {
      const inputEl = input({
        type: 'hidden',
        name: 'select_all',
        value: '1',
      });
      this._actionFormEl.appendChild(inputEl.toDOM());
    } else {
      this._selectedSet.forEach((key, value) => {
        const inputEl = input({
          type: 'hidden',
          name: 'pk',
          value: value,
        });
        this._actionFormEl.appendChild(inputEl.toDOM());
      });
    }
  }
}
