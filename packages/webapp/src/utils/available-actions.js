import { useEffect, useState } from 'react';

import request from './request';

// Card actions offered by the running core modules and enabled plugins, fetched once per page load.
let pending = null;

// The catalog: [{ id, description, args (JSON schema) }].
const fetchActionCatalog = () => {
  if (pending === null) {
    pending = request('listActions').then(({ result }) => result || []);
  }
  return pending;
};

const fetchAvailableActions = () => fetchActionCatalog().then((actions) => new Set(actions.map(({ id }) => id)));

const useAvailableActions = () => {
  const [actions, setActions] = useState(new Set());

  useEffect(() => {
    let active = true;
    fetchAvailableActions().then(available => {
      if (active) setActions(available);
    });
    return () => {
      active = false;
    };
  }, []);

  return actions;
};

const useActionCatalog = () => {
  const [actions, setActions] = useState([]);

  useEffect(() => {
    let active = true;
    fetchActionCatalog().then((catalog) => {
      if (active) setActions(catalog);
    });
    return () => {
      active = false;
    };
  }, []);

  return actions;
};

export {
  fetchActionCatalog,
  fetchAvailableActions,
  useActionCatalog,
  useAvailableActions,
};
