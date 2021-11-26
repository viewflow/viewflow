/* eslint-env browser */

class DOMBuilder {
  constructor(tagName, attrs) {
    this.tagName = tagName;
    this.attrs = attrs;
    this.content = null;
    this.textContent = null;
  }

  with(content) {
    if (!(content instanceof Array)) {
      content = [content];
    }
    this.content = content;
    return this;
  }

  text(textContent) {
    this.textContent = textContent;
    return this;
  }

  _createElement(tagName) {
    return document.createElement(tagName);
  }

  _setAttribute(element, attr, value) {
    element.setAttribute(attr, value);
  }

  toDOM() {
    const element = this._createElement(this.tagName);
    if (this.textContent) {
      element.textContent = this.textContent;
    }

    for (const attr in this.attrs) {
      if (this.attrs.hasOwnProperty(attr)) {
        let value = this.attrs[attr];

        if (value === undefined || value === null) {
          // skip undefined values
          continue;
        } else if (value instanceof Array) {
          // join array data
          value = value.join(' ');
        } else if (typeof(value) === 'boolean') {
          if (value === false) {
            // skip false boolean attributes
            continue;
          } else {
            value = '';
          }
        } else if (! (typeof(value) === 'string' || typeof(value) === 'number')) {
          // join hash key if enabled
          const valuesList = [];
          for (const key in value) {
            if (value.hasOwnProperty(key)) {
              const keyValue = value[key];
              if (keyValue) {
                valuesList.push(key);
              }
            }
          }
          value = valuesList.join(' ');
        }

        this._setAttribute(element, attr, value==null ? '' : value);
      }
    }

    if (this.content) {
      for (let i=0; i<this.content.length; i++) {
        const child = this.content[i];
        if (child) {
          if (child instanceof DOMBuilder) {
            element.appendChild(child.toDOM());
          } else {
            element.appendChild(document.createTextNode(child));
          }
        }
      }
    }

    return element;
  }
}

class SVGBuilder extends DOMBuilder {
  _createElement(tagName) {
    return document.createElementNS('http://www.w3.org/2000/svg', tagName);
  }

  _setAttribute(element, attr, value) {
    element.setAttributeNS(null, attr, value);
  }
}

export function aside(attrs) {
  return new DOMBuilder('aside', attrs);
}

export function div(attrs) {
  return new DOMBuilder('div', attrs);
}

export function p(attrs) {
  return new DOMBuilder('p', attrs);
}

export function a(attrs) {
  return new DOMBuilder('a', attrs);
}

export function button(attrs) {
  return new DOMBuilder('button', attrs);
}

export function label(attrs) {
  return new DOMBuilder('label', attrs);
}

export function input(attrs) {
  return new DOMBuilder('input', attrs);
}

export function select(attrs) {
  return new DOMBuilder('select', attrs);
}

export function optgroup(attrs) {
  return new DOMBuilder('optgroup', attrs);
}

export function option(attrs) {
  return new DOMBuilder('option', attrs);
}

export function i(attrs) {
  return new DOMBuilder('i', attrs);
}

export function svg(attrs) {
  return new SVGBuilder('svg', attrs);
}

export function path(attrs) {
  return new SVGBuilder('path', attrs);
}
