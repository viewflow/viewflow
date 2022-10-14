/* eslint-env browser */
import './index.scss';

export class VFormElement extends HTMLElement {
  connectedCallback() {
    setTimeout(() => {
      this.form = this.querySelector('form');
      this.form.addEventListener('submit', this.onSubmit);
      this.form.querySelectorAll('button[type=submit]').forEach(
          (button) => {
            button.addEventListener('click', this.onButtonClick);
            button.addEventListener('keydown', this.onButtonClick);
          },
      );
    });
  }

  disconnectedCallback() {
    this.form.removeEventListener('submit', this.onSubmit);
    this.form.querySelectorAll('button[type=submit]').forEach(
        (button) => {
          button.removeEventListener('click', this.onButtonClick);
          button.removeEventListener('keydown', this.onButtonClick);
        },
    );
  }

  onSubmit = (event) => {
    if (this.triggerBnt) {
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
