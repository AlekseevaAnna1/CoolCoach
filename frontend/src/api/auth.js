// POST /auth/register → 201 UserRead. Токен регистрация не возвращает.
// POST /auth/login → 200 Token { access_token, token_type: 'bearer' }.
// GET /auth/me → UserRead. Нужен заголовок Authorization: Bearer.
//
// Сброс пароля сознательно не вызывается. Кнопка «Забыли пароль?» только
// открывает место для него: navigate(routes.passwordReset). Когда экран
// появится, сюда лягут два запроса из спецификации:
// 1. POST /auth/password-reset — тело { email }, ответ 202.
// 2. POST /auth/password-reset/confirm — тело { token, new_password }, ответ 204.
// Авторизация на этих двух запросах не нужна. Новый пароль передаётся только
// на втором шаге.

import { request } from './client';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const EMAIL_TAKEN = 'Такой email уже зарегистрирован';
const BAD_LOGIN = 'Неверный email или пароль';

let session = null;

export function getSessionUser() {
  return session ? session.user : null;
}

export function validateName(name) {
  const value = name.trim();
  if (!value) {
    return { name: null, error: null };
  }
  if (value.length > 45) {
    return { name: null, error: 'Имя длиннее 45 символов' };
  }
  return { name: value, error: null };
}

export function validateEmail(email) {
  const value = email.trim();
  if (!value) {
    return 'Укажите email';
  }
  if (value.length > 100) {
    return 'Email длиннее 100 символов';
  }
  if (!EMAIL_PATTERN.test(value)) {
    return 'Некорректный email';
  }
  return null;
}

export function validatePassword(password) {
  if (!password) {
    return 'Укажите пароль';
  }
  if (password.length < 8) {
    return 'Пароль короче 8 символов';
  }
  if (password.length > 72) {
    return 'Пароль длиннее 72 символов';
  }
  return null;
}

function authErrorMessage(error, fallback) {
  if (!error || error.status === 0) {
    return 'Сервер недоступен';
  }
  if (error.status === 409) {
    return EMAIL_TAKEN;
  }
  if (error.status === 401) {
    return BAD_LOGIN;
  }
  return fallback;
}

export async function registerUser({ email, password, name }) {
  const nameCheck = validateName(name ?? '');
  const emailError = validateEmail(email ?? '');
  const passwordError = validatePassword(password ?? '');
  const error = nameCheck.error || emailError || passwordError;
  if (error) {
    return { ok: false, error };
  }

  try {
    const user = await request('/auth/register', {
      method: 'POST',
      body: {
        email: email.trim(),
        password,
        name: nameCheck.name,
      },
    });
    return { ok: true, user };
  } catch (requestError) {
    return {
      ok: false,
      error: authErrorMessage(requestError, 'Не удалось создать аккаунт'),
    };
  }
}

export async function loginUser({ email, password }) {
  const emailError = validateEmail(email ?? '');
  const passwordError = validatePassword(password ?? '');
  const error = emailError || passwordError;
  if (error) {
    return { ok: false, error };
  }

  try {
    const token = await request('/auth/login', {
      method: 'POST',
      body: {
        email: email.trim(),
        password,
      },
    });
    const user = await request('/auth/me', { token: token.access_token });
    session = { token, user };
    return { ok: true, token, user };
  } catch (requestError) {
    session = null;
    return {
      ok: false,
      error: authErrorMessage(requestError, 'Не удалось войти'),
    };
  }
}
