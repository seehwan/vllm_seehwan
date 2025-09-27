import { useState, useCallback, useRef } from 'react';
import { Message, ChatRequest, ChatState } from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const useChat = () => {
  console.log('useChat hook initialized!');
  console.log('API_BASE_URL:', API_BASE_URL);
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    selectedModel: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  // 프로파일 ID에서 실제 모델 ID 가져오기
  const getActualModelId = async (profileId: string): Promise<string | null> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models/status`);
      if (response.ok) {
        const data = await response.json();
        const profile = data.available_profiles?.[profileId];
        return profile?.model_id || null;
      }
    } catch (error) {
      console.error('모델 ID 조회 실패:', error);
    }
    return null;
  };

  // 메시지 추가
  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };

    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, newMessage],
    }));

    return newMessage;
  }, []);

  // 메시지 업데이트
  const updateMessage = useCallback((messageId: string, updates: Partial<Message>) => {
    setChatState(prev => ({
      ...prev,
      messages: prev.messages.map(msg =>
        msg.id === messageId ? { ...msg, ...updates } : msg
      ),
    }));
  }, []);

  // 채팅 요청 전송
  const sendMessage = useCallback(async (content: string, model?: string) => {
    console.log('sendMessage called with content:', content);
    if (!content.trim()) return;

    // 실제 모델 ID 가져오기
    const profileId = model || chatState.selectedModel;
    const actualModelId = profileId ? await getActualModelId(profileId) : null;
    
    if (!actualModelId) {
      setChatState(prev => ({ 
        ...prev, 
        error: '모델을 찾을 수 없습니다. 모델을 다시 선택해주세요.' 
      }));
      return;
    }

    // 사용자 메시지 추가
    const userMessage = addMessage({
      role: 'user',
      content: content.trim(),
      model: profileId || undefined,
    });

    // 어시스턴트 메시지 준비
    const assistantMessage = addMessage({
      role: 'assistant',
      content: '',
      model: profileId || undefined,
    });
    console.log('Assistant message created with ID:', assistantMessage.id);

    // 이전 요청 취소
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // 새 AbortController 생성
    abortControllerRef.current = new AbortController();

    setChatState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const request: ChatRequest = {
        messages: [
          // 기존 메시지들을 vLLM 형식으로 변환
          ...chatState.messages.map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          // 새 사용자 메시지
          {
            role: userMessage.role,
            content: userMessage.content
          }
        ],
        model: actualModelId, // 실제 모델 ID 사용
        stream: false, // 스트리밍 비활성화로 빠른 해결
        temperature: 0.7,
        max_tokens: 2048,
      };

      const token = localStorage.getItem('auth_token');
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // JSON 응답 처리 (stream: false이므로 항상 JSON)
      const result = await response.json();
      const content = result.choices?.[0]?.message?.content || '';
      updateMessage(assistantMessage.id, { 
        content: content,
        tokens: result.usage?.total_tokens || 0
      });

    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request was aborted');
        return;
      }

      console.error('Chat request failed:', error);
      setChatState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Unknown error occurred' 
      }));

      // 에러 발생 시 어시스턴트 메시지 제거
      setChatState(prev => ({
        ...prev,
        messages: prev.messages.filter(msg => msg.id !== assistantMessage.id),
      }));
    } finally {
      setChatState(prev => ({ ...prev, isLoading: false }));
      abortControllerRef.current = null;
    }
  }, [chatState.messages, chatState.selectedModel, addMessage, updateMessage]);

  // 채팅 중단
  const stopChat = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setChatState(prev => ({ ...prev, isLoading: false }));
  }, []);

  // 채팅 초기화
  const clearChat = useCallback(() => {
    setChatState(prev => ({ ...prev, messages: [], error: null }));
  }, []);

  // 모델 설정
  const setModel = useCallback((model: string) => {
    setChatState(prev => ({ ...prev, selectedModel: model }));
  }, []);

  // 에러 초기화
  const clearError = useCallback(() => {
    setChatState(prev => ({ ...prev, error: null }));
  }, []);

  return {
    ...chatState,
    sendMessage,
    stopChat,
    clearChat,
    setModel,
    clearError,
    addMessage,
    updateMessage,
  };
};
