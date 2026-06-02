'use client';

import { useCallback } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { api } from '@/lib/api';
import type { User, TokenPair, ApiResponse } from '@/types';

export function useAuth() {
  const store = useAuthStore();

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.post<ApiResponse<{ user: User; tokens: TokenPair }>>(
        '/auth/login',
        { email, password }
      );
      store.login(response.data.user, response.data.tokens);
      return response.data;
    },
    [store]
  );

  const signup = useCallback(
    async (email: string, password: string, name: string) => {
      const response = await api.post<ApiResponse<{ user: User; tokens: TokenPair }>>(
        '/auth/register',
        { email, password, name }
      );
      store.login(response.data.user, response.data.tokens);
      return response.data;
    },
    [store]
  );

  const loginWithGoogle = useCallback(
    async (idToken: string) => {
      const response = await api.post<ApiResponse<{ user: User; tokens: TokenPair }>>(
        '/auth/login/google',
        { id_token: idToken }
      );
      store.login(response.data.user, response.data.tokens);
      return response.data;
    },
    [store]
  );

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore errors on logout
    }
    store.logout();
  }, [store]);

  const fetchUser = useCallback(async () => {
    try {
      const response = await api.get<ApiResponse<{ user: User }>>('/auth/me');
      store.setUser(response.data.user);
      return response.data.user;
    } catch {
      store.logout();
      return null;
    }
  }, [store]);

  const forgotPassword = useCallback(async (email: string) => {
    await api.post<ApiResponse<{ sent: boolean }>>('/auth/forgot-password', { email });
  }, []);

  const resetPassword = useCallback(async (token: string, newPassword: string) => {
    await api.post<ApiResponse<{ success: boolean }>>('/auth/reset-password', {
      token,
      new_password: newPassword,
    });
  }, []);

  const verifyEmail = useCallback(async (token: string) => {
    await api.post<ApiResponse<{ verified: boolean }>>('/auth/verify-email', { token });
  }, []);

  return {
    ...store,
    login,
    signup,
    loginWithGoogle,
    logout,
    fetchUser,
    forgotPassword,
    resetPassword,
    verifyEmail,
  };
}
