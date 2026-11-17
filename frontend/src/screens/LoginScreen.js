import { useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { loginUser } from '../api/auth';
import { navigate, routes } from '../navigation/routes';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const submitting = useRef(false);

  async function submit() {
    if (submitting.current) {
      return;
    }
    submitting.current = true;
    try {
      const result = await loginUser({ email, password });
      if (!result.ok) {
        setError(result.error);
        return;
      }
      setError('');
      navigate(routes.home);
    } finally {
      submitting.current = false;
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Text>CoolCoach</Text>
      <Text>ТВОЙ УМНЫЙ ТРЕНЕР</Text>
      <Text>С возвращением</Text>
      <Text>Камера подскажет технику, а мы сохраним твой прогресс.</Text>

      <View style={styles.field}>
        <Text>Email</Text>
        <TextInput
          accessibilityLabel="Email"
          testID="login_email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          autoCorrect={false}
          keyboardType="email-address"
          maxLength={100}
          placeholder="you@example.com"
          style={styles.input}
        />
      </View>

      <View style={styles.field}>
        <Text>Пароль</Text>
        <TextInput
          accessibilityLabel="Пароль"
          testID="login_password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          maxLength={72}
          placeholder="Минимум 8 символов"
          style={styles.input}
        />
      </View>

      {/* TODO: route PasswordReset.
          Экран не смонтирован. Позже сюда встанут
          POST /auth/password-reset { email } и
          POST /auth/password-reset/confirm { token, new_password }. */}
      <Pressable
        accessibilityRole="button"
        testID="login_forgot"
        onPress={() => navigate(routes.passwordReset)}
        style={styles.forgot}
      >
        <Text>Забыли пароль?</Text>
      </Pressable>

      {error ? <Text testID="login_error">{error}</Text> : null}

      <Pressable
        accessibilityRole="button"
        testID="login_submit"
        onPress={submit}
        style={styles.button}
      >
        <Text>Войти</Text>
      </Pressable>

      <Pressable
        accessibilityRole="button"
        testID="login_go_register"
        onPress={() => navigate(routes.register)}
        style={styles.link}
      >
        <Text>Создать новый аккаунт</Text>
      </Pressable>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: 16,
    gap: 12,
  },
  field: {
    padding: 12,
    gap: 8,
    borderWidth: 1,
  },
  input: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  forgot: {
    alignSelf: 'flex-end',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  button: {
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  link: {
    alignItems: 'center',
    paddingVertical: 8,
  },
});
