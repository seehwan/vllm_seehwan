import { useState, useEffect, useCallback } from 'react';

interface User {
  user_id: string;
  username: string;
  email: string;
}

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  user: User | null;
  isLoading: boolean;
}

export const useAuth = () => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    token: null,
    user: null,
    isLoading: true,
  });

  // 토큰 검증 및 사용자 정보 가져오기
  const validateToken = useCallback(async (token: string) => {
    try {
      const response = await fetch('http://localhost:8080/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const user = await response.json();
        setAuthState({
          isAuthenticated: true,
          token,
          user,
          isLoading: false,
        });
        return true;
      } else {
        // 토큰이 유효하지 않음
        localStorage.removeItem('auth_token');
        setAuthState({
          isAuthenticated: false,
          token: null,
          user: null,
          isLoading: false,
        });
        return false;
      }
    } catch (error) {
      console.error('Token validation error:', error);
      localStorage.removeItem('auth_token');
      setAuthState({
        isAuthenticated: false,
        token: null,
        user: null,
        isLoading: false,
      });
      return false;
    }
  }, []);

  // 초기 로드 시 토큰 확인
  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      validateToken(token);
    } else {
      setAuthState(prev => ({ ...prev, isLoading: false }));
    }
  }, [validateToken]);

  // 로그인
  const login = useCallback(async (token: string) => {
    localStorage.setItem('auth_token', token);
    await validateToken(token);
  }, [validateToken]);

  // 로그아웃
  const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    setAuthState({
      isAuthenticated: false,
      token: null,
      user: null,
      isLoading: false,
    });
  }, []);

  return {
    ...authState,
    login,
    logout,
    validateToken,
  };
};
