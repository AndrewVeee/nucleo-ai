export const default_chat_settings = {
  system: "You are a friendly, concise assistant.",
  temperature: 0.2,
  chat_history: 5,
};

export const stream_settings = JSON.stringify({
  view: 'reg',
  events: [],
  error: null,
});
export const default_message_settings = JSON.stringify({
  events: [],
  error: null,
});
export function get_settings(opts, defaults) {
  let settings = {};
  if (!defaults) defaults = default_chat_settings;
  if (!opts) opts = {};
  for (let key in defaults) {
    if (opts[key] == undefined) {
      settings[key] = defaults[key];
    } else {
      settings[key] = opts[key]
    }
  }
  return settings;
};