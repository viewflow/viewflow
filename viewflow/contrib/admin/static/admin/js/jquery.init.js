/*global jQuery:false*/
'use strict';
/* Puts the included jQuery into our own namespace using noConflict and passing
 * it 'true'. This ensures that the included jQuery doesn't pollute the global
 * namespace (i.e. this preserves pre-existing values for both window.$ and
 * window.jQuery).
 */
window.django = {jQuery: jQuery.noConflict(true)};

const originalReady = django.jQuery.fn.ready;


django.jQuery.fn.ready = function(fn) {
  if (typeof fn === 'function') {
    originalReady.call(this, function() {
      fn.apply(this, arguments);
    });
    window.addEventListener(eventName, fn);
  } else {
    originalReady.apply(this, arguments);
  }
};
