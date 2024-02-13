import WebRouter from './web-router.js';
import AppCache from './cache.js';

export class App {

  constructor(app_init) {
    this.ready = new Promise((res,rej) => { this.ready_res = res });
    this.user = {logged_in: false};
    this.store_prefix = 'app_';
    this.page = null;
    this.api = null;
    this.cache = AppCache;
    this.router = new WebRouter();
    this.mobile = false;

    // Initialize rest of app.
    if (app_init && app_init.init) app_init.init(this, app_init.init.vue);

    window.addEventListener('resize', this.onResize.bind(this));
    this.router.init();
    this.checkLogin();
    this.onResize();
    this.ready_res();
  }

  onResize() {
    this.mobile = window.matchMedia("(max-width: 767px)").matches;
  }
  open(path) {
    return this.router.open(path);
  }
  save_local(attr, value) {
    localStorage.setItem(this.store_prefix + attr, value);
    return value;
  }
  rm_local(attr) {
    localStorage.removeItem(this.store_prefix + attr);
  }
  load_local(attr, def) {
    return localStorage.getItem(this.store_prefix + attr) || def;
  }
  openPage(cmp, opts) {
    this.page = {cmp: cmp, opts: opts || {}};
  }
  closePage() {
    this.page = null;
  }

  auto_refresh(opts) {
    if (!opts) opts = {}
    if (this.refresh_timer) return false;
    this.refresh_timer = setInterval(() => {
      if (this.user.logged_in) this.checkLogin({renew: true});
    }, (opts.minutes || 10) * 60 * 1000);
  }
  logout() {
    console.log("Logging out");
    this.rm_local('auth');
    this.user = {logged_in: false};
    this.page = null;
  }
  setAuthToken(token) {
    if (!token) return false;
    this.api._include.auth = token;
    this.save_local('auth', token);
    return true;
  }
  checkLogin(opts) {
    if (this.no_login) {
      this.user = {logged_in: true, alias: 'Admin'};
      return Promise.resolve(this.user);
    }
    if (!this.api) return Promise.reject({error: 'No api'});
    opts = opts || {};
    this.api._include.auth = this.load_local('auth');
    return this.api.User.status(opts.renew).then((r) => {
      this.user = r;
      if (opts.renew) {
        this.setAuthToken(r.data.token);
      }
    });
  }
  doLogin(email, pass) {
    return this.api.User.login(email, pass).then((r) => {
      this.user = r;
      this.setAuthToken(r.data.token);
      this.onLogin();
      return r;
    });
  }
  onLogin() {
    console.log("Login", this.user);
  }

  list_jobs() {
    this.jobs = [];
  }
}
