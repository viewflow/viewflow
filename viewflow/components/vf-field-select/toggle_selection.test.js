import {test} from 'node:test';
import assert from 'node:assert/strict';

import {toggleSelection} from './toggle_selection.js';

test('deselecting a middle item does not drop the last selected value', () => {
  let selection = [];
  selection = toggleSelection(selection, 0);
  selection = toggleSelection(selection, 1);
  selection = toggleSelection(selection, 2);

  // Deselect the middle item (index 1).
  selection = toggleSelection(selection, 1);

  assert.deepEqual(selection, [0, 2]);
});

test('selecting keeps a numeric, not lexicographic, order', () => {
  let selection = [];
  selection = toggleSelection(selection, 10);
  selection = toggleSelection(selection, 2);

  assert.deepEqual(selection, [2, 10]);
});
