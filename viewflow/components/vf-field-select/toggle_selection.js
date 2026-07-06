/**
 * Toggle `index` in/out of a multi-select's selection array.
 *
 * Extracted from MDCSelectFoundation.toggleSelectedIndex so the pure
 * array logic can be unit tested without a DOM/MDC adapter.
 */
export function toggleSelection(currentSelection, index) {
  let selection = currentSelection;
  if (selection === undefined) {
    selection = [];
  } else if (typeof selection === 'number') {
    selection = [selection];
  }

  if (selection.includes(index)) {
    selection.splice(selection.indexOf(index), 1);
  } else {
    selection.push(index);
  }

  selection.sort((a, b) => a - b);
  return selection;
}
