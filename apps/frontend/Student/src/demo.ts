import { ref } from 'vue';
import apiClient from '@shared/api-client';
import { auth } from '@shared/auth';

export const demoMode = ref(false);
let configuration: Promise<void> | undefined;

export async function prepareStudentSession(): Promise<void> {
  configuration ??= apiClient.get('/app/config').then(({ data }) => {
    demoMode.value = data.demo_mode === true;
  }).catch((error) => {
    configuration = undefined;
    throw error;
  });
  await configuration;
  if (!demoMode.value) return;

  const { data } = await apiClient.post('/demo/session');
  if (sessionStorage.getItem('coffee_demo_uuid') !== data.uuid) {
    sessionStorage.removeItem('otia_cafe_history');
    sessionStorage.removeItem('otia_cafe_profile');
  }
  sessionStorage.setItem('coffee_demo_uuid', data.uuid);
  auth.setSession(data.access_token, data.role);
}
