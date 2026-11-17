import { useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { registerUser } from '../api/auth';
import { navigate, routes } from '../navigation/routes';

export default function RegisterScreen() {
  const [name, setName] = useState('');
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
      const result = await registerUser({ email, password, name });
      if (!result.ok) {
        setError(result.error);
        return;
      }
      setError('');
      navigate(routes.login);
    } finally {
      submitting.current = false;
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Text>CoolCoach</Text>
      <Text>ТВОЙ УМНЫЙ ТРЕНЕР</Text>
      <Text>Сильнее с каждым движением</Text>
      <Text>Камера подскажет технику, а мы сохраним твой прогресс.</Text>

      <View style={styles.field}>
        <Text>Имя</Text>
        <TextInput
          accessibilityLabel="Имя"
          testID="register_name"
          value={name}
          onChangeText={setName}
          maxLength={45}
          style={styles.input}
        />
      </View>

      <View style={styles.field}>
        <Text>Email</Text>
        <TextInput
          accessibilityLabel="Email"
          testID="register_email"
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
          testID="register_password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          maxLength={72}
          placeholder="Минимум 8 символов"
          style={styles.input}
        />
      </View>

      {error ? <Text testID="register_error">{error}</Text> : null}

      <Pressable
        accessibilityRole="button"
        testID="register_submit"
        onPress={submit}
        style={styles.button}
      >
        <Text>Создать аккаунт</Text>
      </Pressable>

      <Pressable
        accessibilityRole="button"
        testID="register_go_login"
        onPress={() => navigate(routes.login)}
        style={styles.link}
      >
        <Text>У меня уже есть аккаунт</Text>
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
