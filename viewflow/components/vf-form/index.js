/* eslint-env browser */
import './index.scss';

export class VFormElement extends HTMLElement {
  connectedCallback() {
    setTimeout(() => {
      this.form = this.querySelector('form');
      this.form.addEventListener('submit', this.onSubmit);
      // Match all buttons (default type is submit) not just explicit type=submit
      this.form.querySelectorAll('button:not([type=button]):not([type=reset])').forEach(
          (button) => {
            button.addEventListener('click', this.onButtonClick);
            button.addEventListener('keydown', this.onButtonClick);
          },
      );
    });
  }

  disconnectedCallback() {
    this.form.removeEventListener('submit', this.onSubmit);
    this.form.querySelectorAll('button:not([type=button]):not([type=reset])').forEach(
        (button) => {
          button.removeEventListener('click', this.onButtonClick);
          button.removeEventListener('keydown', this.onButtonClick);
        },
    );
  }

  onSubmit = (event) => {
    // Preserve the clicked button's name/value as hidden input before disabling
    // This ensures Turbo includes it in FormData even after buttons are disabled
    if (this.triggerBnt) {
      const button = this.triggerBnt.closest('button');
      if (button && button.name) {
        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = button.name;
        hidden.value = button.value || '';
        this.form.appendChild(hidden);
      }
      this.triggerBnt.classList.add('vf-form__button--active');
      this.triggerBnt = null;
    }
    this.querySelectorAll('button').forEach(
        (button) => button.disabled=true,
    );
  }

  onButtonClick = (event) => {
    this.triggerBnt = event.target;
    if ('novalidate' in this.triggerBnt.dataset) {
      this.form.setAttribute('novalidate', '');
    }
  }
}
