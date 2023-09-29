/* eslint camelcase: 0 */
import {gettext, pgettext, get_format} from '../django-i18n';

export default class VFDateUtils {
  static firstDayOfWeek = parseInt(get_format('FIRST_DAY_OF_WEEK'))

  static monthsOfYear = [
    gettext('January'),
    gettext('February'),
    gettext('March'),
    gettext('April'),
    gettext('May'),
    gettext('June'),
    gettext('July'),
    gettext('August'),
    gettext('September'),
    gettext('October'),
    gettext('November'),
    gettext('December'),
  ]

  static monthsOfYearAbbr = [
    pgettext('three letter January', 'Jan'),
    pgettext('three letter February', 'Feb'),
    pgettext('three letter March', 'Mar'),
    pgettext('three letter April', 'Apr'),
    pgettext('three letter May', 'May'),
    pgettext('three letter June', 'Jun'),
    pgettext('three letter July', 'Jul'),
    pgettext('three letter August', 'Aug'),
    pgettext('three letter September', 'Sep'),
    pgettext('three letter October', 'Oct'),
    pgettext('three letter November', 'Nov'),
    pgettext('three letter December', 'Dec'),
  ]

  static daysOfWeek = [
    pgettext('one letter Sunday', 'S'),
    pgettext('one letter Monday', 'M'),
    pgettext('one letter Tuesday', 'T'),
    pgettext('one letter Wednesday', 'W'),
    pgettext('one letter Thursday', 'T'),
    pgettext('one letter Friday', 'F'),
    pgettext('one letter Saturday', 'S'),
  ]

  static daysOfWeekAbbr = [
    pgettext('three letter Sunday', 'Sun'),
    pgettext('three letter Monday', 'Mon'),
    pgettext('three letter Tuesday', 'Tue'),
    pgettext('three letter Wednesday', 'Wed'),
    pgettext('three letter Thursday', 'Thu'),
    pgettext('three letter Friday', 'Fri'),
    pgettext('three letter Saturday', 'Sat'),
  ]

  static formatDate(format, value) {
    let result = '';
    for (let i=0; i< format.length; i++) {
      if (format[i] === '%') {
        switch (format[i+1]) {
          case 'd':
            result += ('0' + value.getDate()).slice(-2);
            break;
          case 'm':
            result += ('0' + (value.getMonth()+1)).slice(-2);
            break;
          case 'b':
            result += VFDateUtils.monthsOfYearAbbr[value.getMonth()];
            break;
          case 'Y':
            result += value.getFullYear();
            break;
          case 'I':
            const twelveHour = value.getHours() % 12 || 12;
            result += ('0' + twelveHour).slice(-2);
            break;
          case 'H':
            result += ('0' + value.getHours()).slice(-2);
            break;
          case 'M':
            result += ('0' + value.getMinutes()).slice(-2);
            break;
          case 'S':
            result += ('0' + value.getSeconds()).slice(-2);
            break;
          case 'p':
            result += value.getHours() >= 12 ? 'pm': 'am';
        }
        i++;
      } else {
        result += format[i];
      }
    }
    return result;
  };

  static parseDateTime(format, value) {
    const splitFormat = format.split(/[.\-/\:\s]/);
    const date = value.split(/[.\-/\:\s]/);
    let day;
    let month;
    let year;
    for (let i=0; i < splitFormat.length; i++) {
      switch (splitFormat[i]) {
        case '%d':
          day = date[i];
          break;
        case '%m':
          month = date[i] - 1;
          break;
        case '%Y':
          year = date[i];
          break;
        case '%b':
          month = VFDateUtils.monthsOfYearAbbr.indexOf(date[i]);
          if (month === -1) {
            throw new Error(`Invalid month abbreviation: ${date[i]}`);
          }
          break;
      }
    }
    return new Date(year, month, day, 0, 0, 0);
  }

  static daysInMonth(year, month) {
    return new Date(year, month+1, 0).getDate();
  }
}
