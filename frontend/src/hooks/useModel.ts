import { useState, useEffect } from 'react';
import { ModelStatus, ModelSwitchRequest } from '../types/model';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const useModel = () => {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [switching, setSwitching] = useState(false);

  // 모델 상태 조회
  const fetchModelStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/models/status`);
      if (response.ok) {
        const data = await response.json();
        setModelStatus(data);
      }
    } catch (error) {
      console.error('모델 상태 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  // 모델 전환
  const switchModel = async (profileId: string) => {
    try {
      setSwitching(true);
      const response = await fetch(`${API_BASE_URL}/api/models/switch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ profile_id: profileId } as ModelSwitchRequest),
      });

      if (response.ok) {
        const data = await response.json();
        
        // 전환 시작 후 상태 업데이트
        if (modelStatus) {
          setModelStatus({
            ...modelStatus,
            status: 'switching',
            message: data.message,
          });
        }

        // 전환 완료 확인을 위한 폴링 시작
        startStatusPolling();
        
        return { success: true, message: data.message };
      } else {
        const error = await response.json();
        return { success: false, message: error.detail || '모델 전환 실패' };
      }
    } catch (error) {
      console.error('모델 전환 실패:', error);
      return { success: false, message: '네트워크 오류' };
    } finally {
      setSwitching(false);
    }
  };

  // 상태 폴링 (모델 전환 중)
  const startStatusPolling = () => {
    const polling = setInterval(async () => {
      await fetchModelStatus();
      
      if (modelStatus?.status === 'running' || modelStatus?.status === 'error') {
        clearInterval(polling);
      }
    }, 3000); // 3초마다 확인

    // 5분 후 자동 중단
    setTimeout(() => clearInterval(polling), 300000);
  };

  useEffect(() => {
    fetchModelStatus();
  }, []);

  return {
    modelStatus,
    loading,
    switching,
    fetchModelStatus,
    switchModel,
  };
};
