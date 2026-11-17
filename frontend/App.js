import { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { routes, subscribe } from './src/navigation/routes';
import ExerciseScreen from './src/screens/ExerciseScreen';
import HomeScreen from './src/screens/HomeScreen';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';

export default function App() {
  const [screen, setScreen] = useState({ route: routes.register, params: {} });

  useEffect(() => subscribe((route, params) => {
    // routes.camera и routes.passwordReset сюда пока не входят.
    // Кнопки уже шлют navigate с этими именами. Экран подключается
    // добавлением ветки на нужный route.
    if (
      route === routes.register
      || route === routes.login
      || route === routes.home
      || route === routes.exercise
    ) {
      setScreen({ route, params });
    }
  }), []);

  let current = <RegisterScreen />;
  if (screen.route === routes.login) {
    current = <LoginScreen />;
  } else if (screen.route === routes.home) {
    current = <HomeScreen />;
  } else if (screen.route === routes.exercise) {
    current = <ExerciseScreen exerciseId={screen.params.exerciseId} />;
  }

  return (
    <>
      {current}
      <StatusBar style="auto" />
    </>
  );
}
