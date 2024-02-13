/*
Entry point of app, so you can:

- Initialize API
- Initialize routes
- Customize "app" to your needs

After this, the Main.vue component will load.
*/

//import MyCmp from './cmp/my-cmp.vue'
import Home from './cmp/home.vue'
import SvgIcon from './cmp/svg-icon.vue'
import AutoTextarea from './cmp/auto-textarea.vue'
import * as LineStream from './lib/streamer.js'
import * as Jobs from './lib/job-queue.js'
import * as DB from './lib/db.js'
import * as Prompt from './lib/prompt-entry.js'
import {TreeStore} from './lib/tree-store.js'
import {AppAPI} from './lib/api.js'
import ModalTextInput from './cmp/modal-text-input.vue'
import ModalDoc from './cmp/modal-doc.vue'
import {marked} from 'marked';

export function init(app, vue) {
  console.log("Initializing App!");
  app.connected = null;
  app.check_con = () => {
    return app.api.send('/state/check_auth', {}).then((r) => {
      app.connected = true;
    }).catch((err) => { app.connected = false; });
  };
  app.debug = false;
  app.store_prefix = 'ast_';
  app.no_login = true;
  app.api_base = app.load_local('api_base', '/api/');
  app.api_key = app.load_local('api_key', 'no_key');
  app.api_model = app.load_local('api_model', 'chat');
  app.ai_tone = app.load_local('ai_tone', 'Reply with a casual tone.');
  app.chat_width = app.load_local('chat_width', '33');

  app.api = new AppAPI(app.api_base, app.api_key);
  app.stream = LineStream;

  app.chat_list = [];
  app.feed = [];
  app.modals = [];
  app.modal_id = 0;
  app.open_modal = (opts, evts) => {
    app.modal_id += 1;
    app.modals.unshift({modal_id: 1, opts: opts, evts: evts});
  };
  app.close_modal = () => { app.modals.splice(0, 1); };
  app.todo_list = [];
  app.doc_list = [];
  app.stream_list = [];

  app.open_entry_id = (id) => {
    console.log(id);
    app.api.send('/store/list', {id: id}).then((r) => {
      app.open_entry(r[0]);
    });
  };
  app.open_entry = (entry) => {
    if (entry.data_type == 'doc') {
      app.open_modal({
        cmp: ModalDoc,
        content: entry.content,
        title: entry.name,
        style: {width: '95%', height: '90vh'},
        multiline: true,
      });
    } else if (entry.data_type == 'todo') {
      app.open_modal({
        cmp: ModalTextInput,
        content: entry.name,
      });
    }
  };
  app.add_entry = (entry) => {
    if (entry.data_type == 'todo') app.todo_list.unshift(entry);
    if (entry.data_type == 'doc') app.doc_list.unshift(entry);
    if (entry.data_type == 'stream') app.stream_list.unshift(entry);
  };
  app.load_data = () => {
    app.api.store_list({data_type: 'todo'}).then((r) => {
      app.todo_list = r;
    });
    app.api.store_list({data_type: 'doc', _exclude: ['content']}).then((r) => {
      app.doc_list = r;
    });
    app.api.store_list({data_type: 'stream'}).then((r) => {
      app.stream_list = r;
    });
    app.api.store_list({data_type: 'chat'}).then((r) => {
      app.chat_list = r;
    });
  };
  app.load_data();
  app.router.add('/', {
    default: true,
    cmp: null,
  });
  app.user = {logged_in: true, alias: 'Admin'};

  //app.router.add('/test/:id', {
  //  cmp: 'test',
  //});

  marked.use({gfm: true, breaks: true});
  let md_renderer = new marked.Renderer();
  window.md_rnd = md_renderer;
  let link = md_renderer.link;
  let img = md_renderer.image;
  md_renderer.image = (href, title, text) => {
    const html = img.call(md_renderer, href, title, text);
    return html.replace(/^<img /, '<img style="max-height: 400px; max-width: 400px;"');
  };
  md_renderer.link = (href, title, text) => {
    const html = link.call(md_renderer, href, title, text);
    return html.replace(/^<a /, '<a target="_blank" rel="nofollow" ');
  };
  app.markdown = (content) => {
    return marked.parse(content || '', {renderer: md_renderer});
  };
  init.vue.component('Home', Home);
  init.vue.component('svg-icon', SvgIcon)
  init.vue.component('AutoTextarea', AutoTextarea);

};
