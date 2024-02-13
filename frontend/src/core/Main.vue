<script>

export default {
  props: ['app'],
  data() {
    return {
      email: '',
      pass: '',
      login_error: null,
      route: this.app.router,
    }
  },
  methods: {
    onLogin: function() {
    },
    doLogin: function() {
      this.login_error = null;
      this.app.doLogin(this.email, this.pass).then((r) => {
        this.onLogin();
      }).catch((err) => {
        console.log(err);
        this.login_error = "Error " + (err.json && err.json.error ? err.json.error : 'Login Error');
      });
    },
  },
  created: function() {
    this.app.checkLogin().then((r) => this.onLogin());
    this.app.auto_refresh();
  },
}
</script>

<template>
<div class="flex-y" style="height: 100%;">
  <div style="padding: 10px; color: white;" v-if="app.header">
    <div class="flex-x">
      <div class="flex-grow">
      </div>
      <div v-if="app.user.logged_in">
        <button @click="app.logout()" class="btn-sm">Log Out</button>
      </div>
    </div>
  </div>
  <div class="flex-y flex-grow">
    <component class="flex-grow" style="overflow-y: auto;"
        :key="app.router.counter"
        :app="app"
        :is="route.cmp" :args="route.args"
        v-if="route.cmp && app">
    </component>
    <Home :app="app" v-else-if="app.user.logged_in">
    </Home>
    <div v-else="" class="p-2 text-center" style="margin-left: auto; margin-right: auto; max-width: 500px;">
      <h3>Log In</h3>
      <div>
        <h5 class="my-2">Email</h5>
        <input type="text" class="form-control p-1" v-model="email" />
      </div>
      <div>
        <h5 class="my-2">Password</h5>
        <input @keypress.enter="doLogin" type="password" class="form-control p-1" v-model="pass" />
      </div>
      <div v-if="login_error" class="p-2 text-center">
        {{login_error}}
      </div>
      <button @click="doLogin">Log In</button>
    </div>
  </div>
</div>
</template>
