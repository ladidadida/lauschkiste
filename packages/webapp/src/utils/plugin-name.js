// The name of a plugin: its translation, else the title the plugin gives itself, else its name made readable
// (never the bare `snake_case` name).
export const readable = (name) => {
  const text = String(name || '').replace(/_/g, ' ').trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
};

export const pluginName = (t, name, title) => t(`settings.plugins.names.${name}`, { defaultValue: title || readable(name) });
