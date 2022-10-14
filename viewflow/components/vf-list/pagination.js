/* eslint-env browser */

export class VListPagination extends HTMLElement {
  connectedCallback() {
    this._pageParamName = this.dataset.listPageParam;
    this._isLastPage = this.dataset.listPageHasNext == '0';
    this._scrollPosition = null;

    setTimeout(() => {
      this._nextPageEl = this.querySelector('.vf-list__pagination-item--next');
      if (this._nextPageEl) {
        this._nextPageEl.addEventListener('click', this.onClick);
      }

      this._prevPageEl = this.querySelector('.vf-list__pagination-item--prev');
      if (this._prevPageEl) {
        this._prevPageEl.addEventListener('click', this.onClick);
      }

      document.querySelector('vf-list').classList.remove('vf-list--paginated');
    });
  }

  disconnectedCallback() {
    if (this._nextPageEl) {
      this._nextPageEl.removeEventListener('click', this.onClick);
    }
    if (this._prevPageEl) {
      this._prevPageEl.removeEventListener('click', this.onClick);
    }
  }

  onClick = (event) => {
    if (!event.currentTarget.dataset.page) {
      return;
    }
    event.preventDefault();

    const searchParams = new URLSearchParams(window.location.search);
    searchParams.set(this._pageParamName, event.currentTarget.dataset.page);
    this._scrollPosition = [window.scrollX, window.scrollY];
    document.addEventListener('turbo:load', this.onTurboLoad);
    document.addEventListener('turbo:before-render', this.onBeforeRender);
    window.Turbo.visit(window.location.pathname + '?' + searchParams.toString(), {action: 'restore'});
  }

  onTurboLoad = () => {
    document.removeEventListener('turbo:load', this.onTurboLoad);
    document.removeEventListener('turbo:before-render', this.onBeforeRender);

    if (this._scrollPosition) {
      if (this._isLastPage) {
        window.scrollTo(
            document.documentElement.scrollWidth - document.documentElement.clientWidth,
            document.documentElement.scrollHeight - document.documentElement.clientHeight);
      } else {
        window.scrollTo(...this._scrollPosition);
      }
      this._scrollPosition = null;
    }
  }

  onBeforeRender = (event) => {
    event.detail.newBody.querySelector('vf-list').classList.add('vf-list--paginated');
  }
}
