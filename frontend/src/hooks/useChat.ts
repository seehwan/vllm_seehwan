import { useState, useCallback, useRef } from 'react';
import { Message, ChatRequest, ChatState } from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export const useChat = () => {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    selectedModel: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  // 메시지 추가
  const addMessage = useCallback((message: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString(),
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
    if (!content.trim()) return;

    // 사용자 메시지 추가
    const userMessage = addMessage({
      role: 'user',
      content: content.trim(),
      model: model || chatState.selectedModel || undefined,
    });

    // 어시스턴트 메시지 준비
    const assistantMessage = addMessage({
      role: 'assistant',
      content: '',
      model: model || chatState.selectedModel || undefined,
    });

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
          ...chatState.messages,
          userMessage,
        ],
        model: model || chatState.selectedModel || undefined,
        stream: true,
        temperature: 0.7,
        max_tokens: 2048,
      };

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // SSE 스트리밍 처리
      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body not available');
      }

      let accumulatedContent = '';
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') break;

            try {
              const parsed = JSON.parse(data);
              if (parsed.choices?.[0]?.delta?.content) {
                const content = parsed.choices[0].delta.content;
                accumulatedContent += content;
                
                // 어시스턴트 메시지 실시간 업데이트
                updateMessage(assistantMessage.id, { content: accumulatedContent });
              }
            } catch (e) {
              console.warn('Failed to parse SSE data:', e);
            }
          }
        }
      }

      // 토큰 정보 업데이트 (있는 경우)
      if (accumulatedContent) {
        updateMessage(assistantMessage.id, { 
          content: accumulatedContent,
          tokens: accumulatedContent.split(/\s+/).length // 간단한 토큰 계산
        });
      }

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
