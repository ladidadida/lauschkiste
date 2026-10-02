import { useTranslation } from 'react-i18next';

import {
  FormControl,
  Grid,
  NativeSelect,
  Typography,
} from '@mui/material';

const NONE = '__none__';

// A labelled select of `options` ({ value, label }); `value` null/undefined selects `emptyLabel`
// (when given) or the placeholder.
const ItemSelect = ({
  emptyLabel,
  label,
  onChange,
  options,
  placeholder,
  value,
}) => {
  const { t } = useTranslation();
  const selected = value ?? NONE;
  const known = selected === NONE || options.some((option) => option.value === selected);

  return (
    <Grid container sx={{ alignItems: 'center', marginTop: '10px' }}>
      <Grid size={5}>
        <Typography>{label}</Typography>
      </Grid>
      <Grid size={7}>
        <FormControl fullWidth>
          <NativeSelect
            inputProps={{ 'aria-label': label }}
            onChange={(event) => onChange(event.target.value === NONE ? undefined : event.target.value)}
            value={selected}
          >
            <option value={NONE} disabled={!emptyLabel}>
              {emptyLabel || placeholder || t('cards.controls.item-select.placeholder')}
            </option>
            {!known &&
              <option value={selected}>
                {t('cards.controls.item-select.unknown', { value: selected })}
              </option>
            }
            {options.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </NativeSelect>
        </FormControl>
      </Grid>
    </Grid>
  );
};

export default ItemSelect;
