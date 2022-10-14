import VFDateUtils from './date-utils';
import {createSignal} from 'solid-js';
import cc from 'classcat';


const Calendar = (props) => {
  let initialDate = props.value ? VFDateUtils.parseDateTime(props.format, props.value) : NaN;

  if (props.value === '') {
    initialDate = new Date();
  }

  const [getState, setState] = createSignal(isNaN(initialDate) ? {
    'year': new Date().getFullYear(),
    'month': new Date().getMonth(),
    'selected': NaN,
  } : {
    'year': initialDate.getFullYear(),
    'month': initialDate.getMonth(),
    'selected': initialDate,
  });

  if (!isNaN(initialDate)) {
    props.onChange(VFDateUtils.formatDate(props.format, initialDate));
  }

  const changeMonth = (shift) => {
    let currentYear = getState().year;
    let currentMonth = getState().month + shift;
    if (currentMonth < 0) {
      currentYear -= 1;
      currentMonth = 11;
    } else if (currentMonth>11) {
      currentMonth = 0;
      currentYear += 1;
    }

    setState((state) => { return {...state, year: currentYear, month: currentMonth}});
    if (getState().selected) {
      changeDay(getState().selected.getDate());
    }
  };

  const changeDay = (day) => {
    const newDate = new Date(getState().year, getState().month, day);
    props.onChange(isNaN(newDate) ? false : VFDateUtils.formatDate(props.format, newDate));
    setState((state) => { return {...state, 'selected': newDate}});
  };

  const onPrevMonthClick = (event) => {
    changeMonth(-1);
  };

  const onNextMonthClick = (event) => {
    changeMonth(+1);
  };

  const onSurfaceClick = (event) => {
    if (props.disabled || event.target.tagName != 'SPAN') {
      return;
    };
    const day = parseInt(event.target.textContent);
    if (!isNaN(day)) {
      changeDay(day);
    };
  };

  const monthDays = (props) => {
    const startPos = new Date(getState().year, getState().month, 1).getDay() - VFDateUtils.firstDayOfWeek;
    const daysInMonth = VFDateUtils.daysInMonth(getState().year, getState().month);

    return [0, 1, 2, 3, 4, 5].map((week) => {
      return (
        <div class="vf-calendar__row">
          {
            [0, 1, 2, 3, 4, 5, 6].map((day) => {
              const cell = week*7+day;
              const label = cell >= startPos && cell < daysInMonth + startPos ? cell - startPos + 1 :'';

              return <div class={cc({
                'vf-calendar__day': true,
                'vf_calendar__current': label === (getState().selected ? getState().selected.getDate() : NaN),
              })}><span>{ label }</span></div>;
            })
          }
        </div>
      );
    });
  };

  return (
    <div class={cc({
      'vf-calendar': true,
      'vf-calendar--disabled': !!props.disabled,
    })}>
      { props.header ?
      <div class="vf-calendar-header">
        <div class="vf-calendar-header__date mdc-typography--headline4">
          <div class="vf-calendar-header__weekday">
            { getState().selected ? VFDateUtils.daysOfWeekAbbr[getState().selected.getDay()] + ',' : '' }
          </div>
          <div class="vf-calendar-header__day">
            { getState().selected ?
              VFDateUtils.monthsOfYearAbbr[getState().selected.getMonth()] + ' ' + getState().selected.getDate() :
             ''}
          </div>
        </div>
      </div> : '' }
      <div class="vf-calendar__body">
        <div class='vf-calendar__surface' onclick={onSurfaceClick}>
          <div class='vf-calendar__month vf-calendar__month--current'>
            <div class="vf-calendar__title">{`${VFDateUtils.monthsOfYear[getState().month]} ${getState().year}`}</div>
            <div class="vf-calendar__grid">
              <div class="vf-calendar__weekdays">{
                [0, 1, 2, 3, 4, 5, 6].map((weekday) =>
                  <div class="vf-calendar__weekday">{
                    VFDateUtils.daysOfWeek[(weekday + VFDateUtils.firstDayOfWeek) % 7]
                  }</div>,
                )
              }</div>
              <div class="vf_calendar__days">{ monthDays(props) }</div>
            </div>
          </div>
        </div>
        { props.actions ?
          <div class="vf-calendar__actions">
            <button
              type_="button"
              class="mdc-button mdc-dialog__footer__button"
              data-mdc-dialog-action="close">
              <div class="mdc-button__ripple"></div>
              <span class="mdc-button__label">cancel</span>
              <div class="mdc-button__touch"></div>
            </button>
            <button
              type_="button"
              class="mdc-button mdc-dialog__footer__button"
              data-mdc-dialog-action="accept" data-mdc-dialog-button-default data-mdc-dialog-initial-focus>
              <div class="mdc-button__ripple"></div>
              <span class="mdc-button__label">ok</span>
              <div class="mdc-button__touch"></div>
            </button>
          </div> :''}
        { !props.disabled ?
          <>
            <button
              class="mdc-button mdc-button--compact vf-calendar__prev"
              type="button"
              onClick={onPrevMonthClick}>
              <div class="mdc-button__ripple"></div>
              <span class="mdc-button__label material-icons">chevron_left</span>
              <div class="mdc-button__touch"></div>
            </button>
            <button
              class="mdc-button mdc-button--compact vf-calendar__next"
              type="button"
              onClick={onNextMonthClick}>
              <div class="mdc-button__ripple"></div>
              <span class="mdc-button__label material-icons">chevron_right</span>
              <div class="mdc-button__touch"></div>
            </button>
          </> : ''}
      </div>
    </div>
  );
};

export default Calendar;
