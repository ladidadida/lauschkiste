import { useCallback, useContext, useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Keyboard from 'react-simple-keyboard';
import 'react-simple-keyboard/build/css/index.css';

import AppSettingsContext from '../../context/appsettings/context';
import { isKiosk } from './kiosk';
import { display, layoutFor } from './layouts';
import { deleteBackward, insertText, isEditable, pressEnter } from './typing';
import './keyboard.css';

const WATCH_MS = 400;

// Keyboard for the display attached to the box (kiosk mode): it appears while a text field has the focus.
const OnScreenKeyboard = () => {
  const { i18n } = useTranslation();
  const { settings } = useContext(AppSettingsContext);
  const enabled = settings.on_screen_keyboard !== false && isKiosk();
  const [target, setTarget] = useState(null);
  const [layout, setLayout] = useState('default');
  const root = useRef(null);

  useEffect(() => {
    if (!enabled) return undefined;
    const onFocus = ({ target: element }) => {
      if (isEditable(element)) {
        setTarget(element);
        setLayout('default');
      }
    };
    const onBlur = () => setTimeout(() => {
      if (!isEditable(document.activeElement)) setTarget(null);
    }, 0);
    document.addEventListener('focusin', onFocus);
    document.addEventListener('focusout', onBlur);
    return () => {
      document.removeEventListener('focusin', onFocus);
      document.removeEventListener('focusout', onBlur);
    };
  }, [enabled]);

  useEffect(() => {
    if (!target) return undefined;
    const watch = setInterval(() => {
      if (!target.isConnected) setTarget(null);
    }, WATCH_MS);
    return () => clearInterval(watch);
  }, [target]);

  useEffect(() => {
    const { documentElement, body } = document;
    if (!target || !root.current) {
      documentElement.style.removeProperty('--keyboard-height');
      body.classList.remove('keyboard-open');
      return undefined;
    }
    const height = root.current.offsetHeight;
    documentElement.style.setProperty('--keyboard-height', `${height}px`);
    body.classList.add('keyboard-open');
    target.scrollIntoView({ block: 'center' });
    return () => {
      documentElement.style.removeProperty('--keyboard-height');
      body.classList.remove('keyboard-open');
    };
  }, [target]);

  const onKeyPress = useCallback((button) => {
    if (!target) return;
    if (button === '{shift}') setLayout((current) => (current === 'shift' ? 'default' : 'shift'));
    else if (button === '{symbols}') setLayout((current) => (current === 'symbols' ? 'default' : 'symbols'));
    else if (button === '{close}') target.blur();
    else if (button === '{bksp}') deleteBackward(target);
    else if (button === '{enter}') pressEnter(target);
    else {
      insertText(target, button === '{space}' ? ' ' : button);
      if (layout === 'shift') setLayout('default');
    }
  }, [target, layout]);

  if (!enabled || !target) return null;

  return (
    <div
      className="on-screen-keyboard"
      onMouseDown={(event) => event.preventDefault()}
      ref={root}
      role="application"
    >
      <Keyboard
        display={display}
        layout={layoutFor(i18n.language)}
        layoutName={layout}
        mergeDisplay
        onKeyPress={onKeyPress}
        preventMouseDownDefault
      />
    </div>
  );
};

export default OnScreenKeyboard;
