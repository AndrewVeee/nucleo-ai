import {LineStream} from './streamer.js';
export class AppAPI {

  constructor(api_base, api_key) {
    this.api_base = api_base;
    this.api_key = api_key;
  }

  req_gen(path, body, method, req, opts) {
    if (!opts) opts = {};
    if (!req) req = {}
    let headers = {};
    if (!opts.no_ct) {
      headers['content-type'] = opts.contentType || 'application/json';
    }
    if (this.api_key) headers.authorization = 'Bearer ' + this.api_key;
    return {
      url: this.api_base + path,
      req: {
        method: method || 'POST',
        body: JSON.stringify(body),
        headers: new Headers(headers),
        ...req
      }
    }
  }

  store_list(opts) {
    if (!opts) opts = {};
    let args = {};
    for (let attr of ['data_type', 'root_id', 'parent_type', 'parent_id', 'id', '_exclude']) {
      if (opts[attr]) args[attr] = opts[attr];
    }
    return this.send('/store/list', args);
  }
  send(path, body, opts) {
    if (!opts) opts = {};
    let req = this.req_gen(path, body, opts.method, opts.request);
    return fetch(req.url, req.req).then((r) => {
      return r.json();
    });
  }

  upload(path, form_data, opts) {
    if (!opts) opts = {};
    let data = new FormData();
    for (let key in form_data) {
      data.append(key, form_data[key]);
    }
    let req = this.req_gen(path, {}, opts.method, opts.request, opts);
    req.req.body = data;
    return fetch(req.url, req.req).then((r) => {
      return r.json();
    });
  }

  completion(messages, model, opts) {
    if (!opts) opts = {};
    let req = this.req_gen('/v1/chat/completions', {
      messages: messages,
      model: model,
      ...opts,
    });
    return new CompletionStream(req.url, req.req);
  }

}

export class StreamResponse {
  constructor(evt_handler) {
    this.response = '';
    this.state = [];
    this.status = '';
    this.entries = [];
    this.evt_handler = evt_handler;
  }

  as_metadata() {
    return {
      entries: this.entries,
    }
  }
  event(evt) {
    if (this.evt_handler) this.evt_handler(evt);
  }
  handle_assistant(msg) {
    if (msg.event == 'new_entry') {
      this.entries.push(msg.data);
      this.event({name: 'new_entry', content: msg.data});
    } else if (msg.event == 'status') {
      this.status = msg.data.value;
      this.event({name: 'status', content: this.status});
    } else if (msg.event == 'state') {
      this.state[msg.data.level] = msg.data.msg;
      this.event({name: 'state', content: this.state});
    } else if (msg.event) {
      this.event({name: msg.event, content: msg.data});
    }
  }
  add(line) {
    if (line.fn) {
      if (line.fn.name == 'assistant') this.handle_assistant(line.fn.arguments);
    }
    if (line.content) {
      this.response += line.content;
      this.event({name: 'content', content: line.content});
    }
  }
}
function parse_line(line) {
  let data = {parsed: null, content: null, fn: null, line: line, error: null};
  try {
    let m = /^data: (.*)\r?$/.exec(line);
    if (m) {
      if (m[1] != '[DONE]') {
        data.parsed = JSON.parse(m[1]);
      }
    } else if (line.startsWith(': ping') ||
        line.trim() == '') {
    } else {
      data = {choices: [{delta: {content: "\n?? " + line + "\n"}}]};
    }
  } catch {
    data.error = true;
  }
  let delta = data.parsed?.choices?.[0]?.delta || {};
  data.content = delta.content;
  data.fn = delta.function_call;

  return data;
}

class CompletionStream {
  constructor(url, params) {
    this.url = url;
    this.params = params;
    this.promise = new Promise((res,rej) => {
      this.promise_res = res;
      this.promise_rej = rej;
    });
  }

  on_line(line) {
    let data = parse_line(line);
    this.handle_line(data);
  }
  on_done(err) {
    console.log("Done", err);
    if (err)
      this.promise_rej(err);
    else
      this.promise_res(err);
  }
  run(handle_line) {
    this.handle_line = handle_line;
    this.stream = new LineStream(
      this.url, this.params
    );
    this.stream.run(this.on_line.bind(this), this.on_done.bind(this));
    return this.promise;
  }
}