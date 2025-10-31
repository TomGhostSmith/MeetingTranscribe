import { createApp, ref } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import './plugins/element.js'
import installElementPlus from './plugins/element'

const app = createApp(App)
const axios = require('axios')
// axios.default.baseURL = 'http://10.138.42.155/'
installElementPlus(app)
app.use(router)
app.use(store).use(router).mount('#app')
app.config.globalProperties.$backend = ref("http://10.138.42.155:8086/")
// app.config.globalProperties.$backend = "http://192.168.1.155:8086/"
// app.config.globalProperties.$backend = "http://localhost:8086/"
app.config.globalProperties.$axios = axios
axios.defaults.withCredentials = true
axios.interceptors.request.use(
    config => {
        const token = sessionStorage.getItem('token');
        // console.log(token)
        if (token != null) {
            config.headers.token = token;
        }
        else {
            config.headers.token = undefined;
        }
        // console.log(config.headers.token)
        // console.log(config)
        return config;
    },
    error => {
        return Promise.error(error);
    }
)