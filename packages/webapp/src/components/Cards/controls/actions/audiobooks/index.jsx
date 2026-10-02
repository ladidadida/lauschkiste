import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import CommandSelector from '../../command-selector';
import ItemSelect from '../../item-select';
import request from '../../../../../utils/request';
import { getActionAndCommand } from '../../../utils';

const SelectAudiobooks = ({
  actionData,
  handleActionDataChange,
}) => {
  const { t } = useTranslation();
  const [books, setBooks] = useState([]);
  const { action, command } = getActionAndCommand(actionData);
  const book = actionData.command?.args?.book;

  useEffect(() => {
    request('audiobooksList').then(({ result }) => setBooks(result || []));
  }, []);

  return (
    <>
      <CommandSelector
        actionData={actionData}
        handleActionDataChange={(nextAction, nextCommand) => (
          handleActionDataChange(nextAction, nextCommand, { book })
        )}
      />
      {command &&
        <ItemSelect
          label={t('cards.controls.actions.audiobooks.book')}
          onChange={(value) => handleActionDataChange(action, command, { book: value })}
          options={books.map(({ book: value, title }) => ({ value, label: title }))}
          placeholder={books.length ? undefined : t('cards.controls.actions.audiobooks.none')}
          value={book}
        />
      }
    </>
  );
};

export default SelectAudiobooks;
