import React, { useEffect } from 'react';

export const OAuthCallback: React.FC = () => {
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const error = urlParams.get('error');

    if (token) {
      // 토큰을 localStorage에 저장
      localStorage.setItem('auth_token', token);
      
      // 메인 페이지로 리다이렉트
      window.location.href = '/';
    } else if (error) {
      // 에러 처리
      console.error('OAuth error:', error);
      alert('로그인 중 오류가 발생했습니다.');
      window.location.href = '/';
    }
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">로그인 처리 중...</p>
      </div>
    </div>
  );
};
