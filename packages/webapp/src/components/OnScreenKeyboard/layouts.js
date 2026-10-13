const symbols = [
  '1 2 3 4 5 6 7 8 9 0',
  '- / : ; ( ) € & @ "',
  '. , ? ! \' # + = %',
  '{abc} {space} {bksp}',
];

const german = {
  default: [
    'q w e r t z u i o p ü',
    'a s d f g h j k l ö ä',
    '{shift} y x c v b n m ß {bksp}',
    '{symbols} {space} . - {close} {enter}',
  ],
  shift: [
    'Q W E R T Z U I O P Ü',
    'A S D F G H J K L Ö Ä',
    '{shift} Y X C V B N M ẞ {bksp}',
    '{symbols} {space} . - {close} {enter}',
  ],
  symbols,
};

const english = {
  default: [
    'q w e r t y u i o p',
    'a s d f g h j k l',
    '{shift} z x c v b n m {bksp}',
    '{symbols} {space} . - {close} {enter}',
  ],
  shift: [
    'Q W E R T Y U I O P',
    'A S D F G H J K L',
    '{shift} Z X C V B N M {bksp}',
    '{symbols} {space} . - {close} {enter}',
  ],
  symbols,
};

export const display = {
  '{bksp}': '⌫',
  '{close}': '⌄',
  '{enter}': '⏎',
  '{shift}': '⇧',
  '{space}': ' ',
  '{symbols}': '123',
  '{abc}': 'ABC',
};

export const layoutFor = (language = 'en') => {
  const layout = language.startsWith('de') ? german : english;
  return {
    default: layout.default,
    shift: layout.shift,
    symbols: layout.symbols.map((row) => row.replace('{abc}', '{symbols}')),
  };
};
