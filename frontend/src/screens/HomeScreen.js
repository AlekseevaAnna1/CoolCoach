import { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { loadCurrentUser, loadExercises } from '../api/home';
import { parseExerciseText } from '../api/parseExerciseText';
import { ALL_MUSCLES, MUSCLE_FILTERS, muscleLabel } from '../constants/muscleGroups';
import { navigate, routes } from '../navigation/routes';

export default function HomeScreen() {
  const user = useMemo(() => loadCurrentUser(), []);
  const exercises = useMemo(() => loadExercises(), []);
  const [query, setQuery] = useState('');
  const [muscle, setMuscle] = useState(ALL_MUSCLES);

  const visibleExercises = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return exercises.filter((exercise) => {
      const matchesMuscle = muscle === ALL_MUSCLES || exercise.target_muscle_group === muscle;
      const haystack = `${exercise.name} ${exercise.description ?? ''}`.toLowerCase();
      const matchesQuery = normalizedQuery.length === 0 || haystack.includes(normalizedQuery);
      return matchesMuscle && matchesQuery;
    });
  }, [exercises, muscle, query]);

  const displayName = user.name && user.name.trim() ? user.name.trim() : null;
  const avatarSource = displayName || user.email || '';
  const avatarLetter = avatarSource ? avatarSource.charAt(0).toUpperCase() : '?';

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text>ДОБРОЕ УТРО</Text>
          <Text>{displayName ? `Готов двигаться, ${displayName}?` : 'Готов двигаться?'}</Text>
        </View>
        {/* TODO: route Profile */}
        <Pressable
          accessibilityRole="button"
          testID="home_avatar"
          onPress={() => navigate(routes.profile)}
          style={styles.avatar}
        >
          <Text>{avatarLetter}</Text>
        </Pressable>
      </View>

      <TextInput
        accessibilityRole="search"
        testID="home_search"
        value={query}
        onChangeText={setQuery}
        placeholder="Найти упражнение"
        style={styles.search}
      />

      <Text>Группа мышц</Text>
      <View style={styles.chips}>
        {MUSCLE_FILTERS.map((filter) => {
          const selected = muscle === filter.id;
          return (
            <Pressable
              key={filter.id}
              accessibilityRole="button"
              accessibilityState={{ selected }}
              testID={`home_muscle_${filter.id}`}
              onPress={() => setMuscle(filter.id)}
              style={[styles.chip, selected ? styles.chipSelected : null]}
            >
              <Text>{filter.label}</Text>
            </Pressable>
          );
        })}
      </View>

      <Text>Упражнения</Text>
      {visibleExercises.map((exercise) => {
        const summary = parseExerciseText(exercise.description).description;
        return (
        <View key={exercise.exercise_id} style={styles.card}>
          {/* TODO: route Workout */}
          <Pressable
            accessibilityRole="button"
            testID={`home_exercise_start_${exercise.exercise_id}`}
            onPress={() => navigate(routes.workout, { exerciseId: exercise.exercise_id })}
            style={styles.start}
          >
            <Text>Старт</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            testID={`home_exercise_open_${exercise.exercise_id}`}
            onPress={() => navigate(routes.exercise, { exerciseId: exercise.exercise_id })}
            style={styles.cardBody}
          >
            {exercise.target_muscle_group ? (
              <Text>{muscleLabel(exercise.target_muscle_group)}</Text>
            ) : null}
            <Text>{exercise.name}</Text>
            {summary ? <Text numberOfLines={2}>{summary}</Text> : null}
          </Pressable>
        </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: 16,
    gap: 12,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerText: {
    flex: 1,
    marginRight: 12,
  },
  avatar: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  search: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  chipSelected: {
    borderWidth: 1,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 8,
  },
  start: {
    width: 64,
    height: 64,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardBody: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderWidth: 1,
  },
});
