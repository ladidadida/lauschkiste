import commands from "../commands";

const REQUEST_TIMEOUT_MS = 15000;

// GET requests carry kwargs as query params (repeated for array values, matching FastAPI's
// convention for List[...] Query params); undefined/null values are omitted rather than sent
// as the literal string 'undefined'/'null'.
const toQueryString = (kwargs) => {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(kwargs)) {
    if (value === undefined || value === null) {
      continue;
    }
    if (Array.isArray(value)) {
      value.forEach((entry) => params.append(key, entry));
    }
    else {
      params.append(key, value);
    }
  }
  return params.toString();
};

// `{name}` placeholders in a path are filled from (and removed from) kwargs.
const fillPath = (path, kwargs) => {
  const remaining = { ...kwargs };
  const filled = path.replace(/\{(\w+)\}/g, (_, name) => {
    const value = remaining[name];
    delete remaining[name];
    return encodeURIComponent(value);
  });
  return [filled, remaining];
};

const restRequest = async ({ method, path }, allKwargs) => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  const options = { method, signal: controller.signal };
  const [filledPath, kwargs] = fillPath(path, allKwargs);
  let requestPath = filledPath;
  if (method === 'GET') {
    const query = toQueryString(kwargs);
    if (query) {
      requestPath = `${requestPath}?${query}`;
    }
  }
  else {
    options.headers = { 'Content-Type': 'application/json' };
    options.body = JSON.stringify(kwargs);
  }

  try {
    const response = await fetch(requestPath, options);
    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new Error(`Request failed with HTTP ${response.status}${body ? `: ${body}` : ''}`);
    }
    if (response.status === 204) {
      return null;
    }
    return await response.json();
  }
  catch (error) {
    if (error && error.name === 'AbortError') {
      throw new Error('Request timed out');
    }
    throw error;
  }
  finally {
    clearTimeout(timeout);
  }
};

const request = async (command, kwargs = {}) => {
  try {
    if (!(command in commands)) {
      throw new Error(`'${command}' does not exist in command object`);
    }

    const result = await restRequest(commands[command].rest, kwargs);
    return { result };
  }
  catch (error) {
    console.error(`${command}: `, error);
    return { error };
  };
};

// The message of an API error ({"error": {"message"}}) carried by a failed request, if any.
const requestErrorMessage = (error) => {
  const body = String(error?.message || '').split(': ').slice(1).join(': ');
  try {
    return JSON.parse(body)?.error?.message || null;
  }
  catch {
    return null;
  }
};

export { requestErrorMessage };
export default request;
