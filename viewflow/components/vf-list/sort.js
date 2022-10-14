/* eslint-env browser */

export class VList extends HTMLElement {
  connectedCallback() {
    this._orderByParamName = this.dataset.listSortOrderParam;
    this._pageParamName = this.dataset.listSortPageParam;
    this._scrollPosition = null;

    setTimeout(() => {
      this._headEl = this.querySelector('thead');
      this._headEl.addEventListener('click', this.onHeadClick);
      this._headEl.addEventListener('mousedown', this.onHeadSelectStart);
    });
  }

  disconnectedCallback() {
    this._headEl.removeEventListener('mousedown', this.onHeadSelectStart);
    this._headEl.removeEventListener('click', this.onClick);
  }

  onHeadSelectStart = (event) => {
    if (!event.target.closest('.mdc-select')) {
      event.preventDefault();
    }
  }

  onTurboLoad = () => {
    document.removeEventListener('turbo:load', this.onTurboLoad);
    if (this._scrollPosition) {
      window.scrollTo(...this._scrollPosition);
      this._scrollPosition = null;
    }
  }

  onHeadClick = (event) => {
    if (!event.target.dataset.listSortColumn) {
      return;
    }

    // collect current sort
    const headers = [].slice.call(
        this.querySelectorAll('.vf-list__table-header--sortable[data-list-sort-position]'),
    );
    headers.sort((a, b) => a.dataset.listSortPosition - b.dataset.listSortPosition);

    // current columns order
    const orderBy = {};
    headers.forEach((header) => {
      if (header.classList.contains('vf-list__table-header--sort-asc')) {
        orderBy[header.dataset.listSortColumn] = 'asc';
      } else if (header.classList.contains('vf-list__table-header--sort-desc')) {
        orderBy[header.dataset.listSortColumn] = 'desc';
      }
    });

    // current columns positions
    const columnOrder = headers.map((elem) => elem.dataset.listSortColumn);

    // toggle search
    const searchParams = new URLSearchParams(window.location.search);

    if (event.target.dataset.listSortColumn in orderBy) {
      if (orderBy[event.target.dataset.listSortColumn] == 'asc') {
        orderBy[event.target.dataset.listSortColumn] = 'desc';
      } else {
        delete orderBy[event.target.dataset.listSortColumn];
      }
    } else {
      orderBy[event.target.dataset.listSortColumn] = 'asc';
      columnOrder.push(event.target.dataset.listSortColumn);
    }

    // combine search query back
    if (event.shiftKey) {
      const orderQuery = columnOrder.map((column) => {
        if (column in orderBy) {
          return (orderBy[column] == 'desc'?'-':'') + column;
        }
        return '';
      }).filter((element) => element).join(',');
      searchParams.set(this._orderByParamName, orderQuery);
    } else if (event.target.dataset.listSortColumn in orderBy) {
      searchParams.set(
          this._orderByParamName,
          (orderBy[event.target.dataset.listSortColumn] == 'desc'?'-':'') + event.target.dataset.listSortColumn);
    } else {
      searchParams.set(this._orderByParamName, '');
    }

    searchParams.delete(this._pageParamName);
    this._scrollPosition = [window.scrollX, window.scrollY];
    document.addEventListener('turbo:load', this.onTurboLoad);
    window.Turbo.visit(window.location.pathname + '?' + searchParams.toString(), {action: 'restore'});
  }
}
