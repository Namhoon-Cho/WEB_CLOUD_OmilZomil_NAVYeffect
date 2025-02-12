import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import store from "./stores";
import VueNumber from 'vue-number-animation'
import VueApexCharts from 'vue3-apexcharts';

import {
    Chart,
    registerables,
  } from 'chart.js'
  Chart.register(...registerables);
  
// Vue
const app = createApp(App)
app.config.globalProperties.$axios = axios; 
app.use(store)
app.use(VueApexCharts)
// app.component
app.use(VueNumber)
app.use(router).mount('#app')

// app.config.globalProperties.$axios = axios.create({
//         timeout: 3000,
//         headers: {
//           // 헤더 세팅
//         },
//         proxy: {
//           // url 리소스를 추가해주자
//           "/user": {
//             // 해당 리소스가 있는 url일 경우 타겟으로 baseURL을 변경
//             target: "http://117.17.110.220:7717/user/",
//             // 기본 베이스URL을 바꿔줄지 여부
//             changeOrigin: true
//           },
//         }
//       })