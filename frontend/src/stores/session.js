import { api } from '../api/client.js';

export const session = { token: sessionStorage.getItem('ct.session'), user: null };
export const request = (path, options = {}) => api(path, { ...options, token: session.token });

export function signIn({ token, user }) {
  session.token = token;
  session.user = user;
  sessionStorage.setItem('ct.session', token);
}

export function signOut() {
  session.token = null;
  session.user = null;
  sessionStorage.removeItem('ct.session');
}
