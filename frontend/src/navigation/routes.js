export const routes = {
  register: 'Register',
  login: 'Login',
  home: 'Home',
  profile: 'Profile',
  exercise: 'Exercise',
  workout: 'Workout',
  // Экран камеры ещё не подключён. Кнопка уже вызывает navigate(routes.camera).
  // Чтобы связь заработала, в App.js нужно отрисовать экран на этот route.
  camera: 'Camera',
  // Экран сброса пароля ещё не подключён. Кнопка «Забыли пароль?» уже вызывает
  // navigate(routes.passwordReset). Дальше два запроса спецификации:
  // POST /auth/password-reset { email } → 202
  // POST /auth/password-reset/confirm { token, new_password } → 204
  passwordReset: 'PasswordReset',
};

const listeners = new Set();

export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

// Call sites stay as navigate(routes.*, params).
// Profile, Workout, Camera and PasswordReset still have no screen: the log is the stub.
export function navigate(route, params) {
  const nextParams = params ?? {};
  console.log(`navigate: ${route}`, nextParams);
  listeners.forEach((listener) => listener(route, nextParams));
}
