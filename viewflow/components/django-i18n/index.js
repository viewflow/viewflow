/* eslint-env browser */
/* eslint camelcase: 0 */

let pluralidx = window.pluralidx;
let gettext = window.gettext;
let ngettext = window.ngettext;
let gettext_noop = window.gettext_noop;
let pgettext = window.pgettext;
let npgettext = window.npgettext;
let get_format = window.get_format;
let interpolate = window.interpolate;


if (!window.django || !window.django.jsi18n_initialized) {
  pluralidx = (count) => (count == 1) ? 0 : 1;
  gettext = (msg) => msg;
  ngettext = (singular, plural, count) => (count == 1) ? singular : plural;
  gettext_noop = (msg) => msg;
  pgettext = (context, msg) => msg;
  npgettext = (context, singular, plural, count) => (count == 1) ? singular : plural;

  const formats = {
    'DATETIME_FORMAT': 'N j, Y, P',
    'DATETIME_INPUT_FORMATS': [
      '%Y-%m-%d %H:%M:%S',
    ],
    'DATE_FORMAT': 'N j, Y',
    'DATE_INPUT_FORMATS': [
      '%Y-%m-%d',
    ],
    'DECIMAL_SEPARATOR': '.',
    'FIRST_DAY_OF_WEEK': 0,
    'MONTH_DAY_FORMAT': 'F j',
    'NUMBER_GROUPING': 3,
    'SHORT_DATETIME_FORMAT': 'm/d/Y P',
    'SHORT_DATE_FORMAT': 'm/d/Y',
    'THOUSAND_SEPARATOR': ',',
    'TIME_FORMAT': 'P',
    'TIME_INPUT_FORMATS': [
      '%H:%M:%S',
    ],
    'YEAR_MONTH_FORMAT': 'F Y',
  };

  get_format = (formatType) => {
    const value = formats[formatType];
    if (typeof(value) == 'undefined') {
      return formatType;
    } else {
      return value;
    }
  };

  interpolate = (fmt, obj, named) => {
    if (named) {
      return fmt.replace(/%\(\w+\)s/g, function(match) {
        return String(obj[match.slice(2, -2)]);
      });
    } else {
      return fmt.replace(/%s/g, function(match) {
        return String(obj.shift());
      });
    }
  };
}

export {
  gettext, pluralidx, ngettext, gettext_noop,
  pgettext, npgettext, get_format, interpolate,
};
