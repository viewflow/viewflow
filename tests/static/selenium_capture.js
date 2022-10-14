window.errors = [];

window.prevOnError = window.onerror;

window.onerror = function(msg, url, line, col, error) {
  errors.push({msg: msg, url: url, line: line});
  if (window.prevOnError) {
    return window.prevOnError(errorMsg, url, lineNumber);
  }
  return false;
};
