const TEXT_TYPES = new Set(['text', 'search', 'url', 'email', 'tel', 'password', 'number', '']);

export const isEditable = (element) => {
  if (!element || element.disabled || element.readOnly) return false;
  if (element.tagName === 'TEXTAREA') return true;
  return element.tagName === 'INPUT' && TEXT_TYPES.has(element.type);
};

// Set the value the way a user typing would, so React's change handlers see it.
const setValue = (element, value, caret) => {
  const prototype = element.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  Object.getOwnPropertyDescriptor(prototype, 'value').set.call(element, value);
  element.dispatchEvent(new Event('input', { bubbles: true }));
  try {
    element.setSelectionRange(caret, caret);
  } catch {
    // number and email inputs have no selection
  }
};

const selection = (element) => {
  const { value } = element;
  const start = element.selectionStart ?? value.length;
  const end = element.selectionEnd ?? value.length;
  return [value, start, end];
};

export const insertText = (element, text) => {
  const [value, start, end] = selection(element);
  setValue(element, value.slice(0, start) + text + value.slice(end), start + text.length);
};

export const deleteBackward = (element) => {
  const [value, start, end] = selection(element);
  if (start !== end) return setValue(element, value.slice(0, start) + value.slice(end), start);
  if (start === 0) return undefined;
  return setValue(element, value.slice(0, start - 1) + value.slice(end), start - 1);
};

// Enter submits a form or ends the input; in a text area it starts a new line.
export const pressEnter = (element) => {
  if (element.tagName === 'TEXTAREA') return insertText(element, '\n');
  const init = { bubbles: true, cancelable: true, key: 'Enter', code: 'Enter', keyCode: 13, which: 13 };
  const proceed = element.dispatchEvent(new KeyboardEvent('keydown', init));
  element.dispatchEvent(new KeyboardEvent('keyup', init));
  if (proceed && element.form) element.form.requestSubmit();
  return element.blur();
};
