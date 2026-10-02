import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

import ItemSelect from '../../item-select';
import request from '../../../../../utils/request';

const SelectRadio = ({
  actionData,
  handleActionDataChange,
}) => {
  const { t } = useTranslation();
  const [stations, setStations] = useState([]);
  const station = actionData.command?.args?.station;

  useEffect(() => {
    request('radioStations').then(({ result }) => setStations(result || []));
  }, []);

  return (
    <ItemSelect
      label={t('cards.controls.actions.radio.station')}
      onChange={(value) => handleActionDataChange('radio', 'radio_play', { station: value })}
      options={stations.map(({ id, name }) => ({ value: id, label: name }))}
      placeholder={stations.length ? undefined : t('cards.controls.actions.radio.none')}
      value={station}
    />
  );
};

export default SelectRadio;
