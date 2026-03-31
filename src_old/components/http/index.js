import auth from './apis/auth_api';
import dashboard from './apis/dashboard_api';
import setting from './apis/setting_api';

let SERVER_ADDER = process.env.VUE_APP_BASE_API;
if (!SERVER_ADDER) {
    SERVER_ADDER = window.location.protocol + "//" + window.location.host + "";
}

let TOKEN = localStorage.getItem('access_token');

export default {
    SERVER_ADDER,
    TOKEN,
    auth,
    dashboard,
    setting,
}