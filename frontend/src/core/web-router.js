export default class WebRouter {

  constructor() {
    this.routes = [];
    this.counter = 0;
    this.default_route = null;
    this.from = WebRouter.FROM_HASH;
    this.current = {cmp: null};
    this.onRoute = null;
    if (typeof(window) != 'undefined') {
      window.addEventListener('popstate', (evt) => {
        this.onPopState(evt);
      });
    }
  }

  init() {
    this.open(null, null, {no_push: true});
  }
  onPopState(evt) {
    this.open(null, null, {no_push: true});
  }
  open(path, params, opts) {
    if (!opts) opts = {};
    if (path && this.from == WebRouter.FROM_HASH && !path.startsWith("#!")) {
      path = "#!" + path
    }
    let route = this.get_route(path, params);

    if (!route) return false;

    if (this.current.unload) {
      let res = this.current.unload();
      if (!res) return false;
    }
    this.current = {route: route.route, cmp: route.route.opts.cmp, args: route.args, opts: opts};
    this.counter += 1;
    if (this.onRoute) this.onRoute(this.current);
    if (!opts.no_push) {
      // TODO: Add URL params
      window.history.pushState({}, '', path);
    }
    return this.current;
  }
  get_route(path, params) {
    if (!path) {
      if (this.from == WebRouter.FROM_HASH) {
        path = document.location.hash.substring(2);
        let q = path.indexOf('?'), query = null;
        if (q) {
          query = path.substring(q+1);
          path = path.replace(/\?.*/, '')
        }
        params = new URLSearchParams(query);
      } else {
        path = document.location.pathname;
        params = document.location.search;
      }
    } else if (path.startsWith("#!")) {
      path = path.substring(2);
    }
    let parts = path.split("/").filter(pt => pt);
    for (let route of this.routes) {
      if (route.parts.length == parts.length) {
        let match = true, vals = {};
        for (let i in parts) {
          let rpart = route.parts[i];
          if (rpart.startsWith(':')) {
            vals[rpart.substring(1)] = parts[i];
          } else if (rpart != parts[i]) {
            match = false;
            break;
          }
        }
        if (match) {
          return {route: route, cmp: route.opts.cmp, args: vals };
        }
      }
    }
    return null;
  }

  add(route_str, opts) {
    if (!opts) opts = {};
    let route = {
      path: route_str,
      parts: route_str.split("/").filter(pt => pt),
      opts: opts,
    };
    this.routes.push(route);
    if (opts.default) this.default_route = route;

  }
}

WebRouter.FROM_LOCATION = 1;
WebRouter.FROM_HASH = 2;
