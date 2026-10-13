import { describe, expect, it, vi } from 'vitest';

import { deleteBackward, insertText, isEditable, pressEnter } from './typing';

const field = (value = '', tag = 'input') => {
  const element = document.createElement(tag);
  document.body.append(element);
  element.value = value;
  return element;
};

describe('typing', () => {
  it('inserts at the caret and sends an input event', () => {
    const element = field('ac');
    element.setSelectionRange(1, 1);
    const listener = vi.fn();
    element.addEventListener('input', listener);
    insertText(element, 'b');
    expect(element.value).toBe('abc');
    expect(element.selectionStart).toBe(2);
    expect(listener).toHaveBeenCalledOnce();
  });

  it('replaces a selection', () => {
    const element = field('abcd');
    element.setSelectionRange(1, 3);
    insertText(element, 'x');
    expect(element.value).toBe('axd');
  });

  it('deletes backward and does nothing at the start', () => {
    const element = field('abc');
    element.setSelectionRange(2, 2);
    deleteBackward(element);
    expect(element.value).toBe('ac');
    element.setSelectionRange(0, 0);
    deleteBackward(element);
    expect(element.value).toBe('ac');
  });

  it('appends where the type has no caret', () => {
    const element = field();
    element.type = 'email';
    insertText(element, 'a');
    insertText(element, 'b');
    expect(element.value).toBe('ab');
  });

  it('submits the form on enter and leaves the field', () => {
    const form = document.createElement('form');
    const element = document.createElement('input');
    form.append(element);
    document.body.append(form);
    form.requestSubmit = vi.fn();
    element.focus();
    pressEnter(element);
    expect(form.requestSubmit).toHaveBeenCalledOnce();
    expect(document.activeElement).not.toBe(element);
  });

  it('starts a new line in a text area', () => {
    const element = field('a', 'textarea');
    element.setSelectionRange(1, 1);
    pressEnter(element);
    expect(element.value).toBe('a\n');
  });

  it('knows which elements take text', () => {
    expect(isEditable(field())).toBe(true);
    const checkbox = field();
    checkbox.type = 'checkbox';
    expect(isEditable(checkbox)).toBe(false);
    const readonly = field();
    readonly.readOnly = true;
    expect(isEditable(readonly)).toBe(false);
    expect(isEditable(document.createElement('div'))).toBe(false);
  });
});
