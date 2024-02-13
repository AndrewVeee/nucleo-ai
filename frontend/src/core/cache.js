
export default class AppCache {

  constructor(opts) {
    if (!opts) opts = {};
    this.items = {};
    this.max = opts.max;
    this.opts = opts;
  }

  add_all(list, id_field) {
    for (let ent of list) this.add(ent[id_field], ent);
  }
  add(id, data) {
    // TODO: If self.max, check for removal.
    this.items[id] = data;
  }

  lookup(id) {
    if (!this.opts.lookup) return Promise.reject({error: 'No lookup function'});
    return this.opts.lookup(id);
  }
  get(id) {
    return new Promise((res,rej) => {
      if (this.items[id]) {
        res(this.items[id]);
        return;
      } else {
        this.lookup(id).then((r) => {
          this.add(id, r);
          res(r);
        }).catch((err) => { rej(err) });
      }
    });
  }

}
