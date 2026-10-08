import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import CommandSelector from '../../command-selector';
import ItemSelect from '../../item-select';
import request from '../../../../../utils/request';
import { getActionAndCommand } from '../../../utils';

// A book of another source is `source/book`, a local one just its folder name.
const toValue = ({ book, source }) => (source && source !== 'local' ? `${source}/${book}` : book);
const toArgs = (value) => {
  const slash = value.indexOf('/');
  return slash < 0 ? { book: value } : { book: value.slice(slash + 1), source: value.slice(0, slash) };
};

const SelectAudiobooks = ({
  actionData,
  handleActionDataChange,
}) => {
  const { t } = useTranslation();
  const [books, setBooks] = useState([]);
  const { action, command } = getActionAndCommand(actionData);
  const args = actionData.command?.args;
  const book = args?.book && toValue(args);

  useEffect(() => {
    request('audiobooksList').then(({ result }) => setBooks(result || []));
  }, []);

  return (
    <>
      <CommandSelector
        actionData={actionData}
        handleActionDataChange={(nextAction, nextCommand) => (
          handleActionDataChange(nextAction, nextCommand, book ? toArgs(book) : {})
        )}
      />
      {command &&
        <ItemSelect
          label={t('cards.controls.actions.audiobooks.book')}
          onChange={(value) => handleActionDataChange(action, command, toArgs(value))}
          options={books.map((entry) => ({ value: toValue(entry), label: entry.title }))}
          placeholder={books.length ? undefined : t('cards.controls.actions.audiobooks.none')}
          value={book}
        />
      }
    </>
  );
};

export default SelectAudiobooks;
