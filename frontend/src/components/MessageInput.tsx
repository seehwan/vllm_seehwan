import React, { useState, useRef, useEffect } from 'react';
import { Send, StopCircle, RotateCcw } from 'lucide-react';

interface MessageInputProps {
  onSendMessage: (message: string) => void;
  onStopChat: () => void;
  onClearChat: () => void;
  isLoading: boolean;
  disabled?: boolean;
}

const MessageInput: React.FC<MessageInputProps> = ({
  onSendMessage,
  onStopChat,
  onClearChat,
  isLoading,
  disabled = false,
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 자동 높이 조정
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleClearChat = () => {
    if (window.confirm('모든 대화를 삭제하시겠습니까?')) {
      onClearChat();
    }
  };

  return (
    <div className="border-t bg-white p-4 flex-shrink-0">
      {/* 에러 메시지나 상태 표시 */}
      {disabled && (
        <div className="mb-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <p className="text-sm text-yellow-800">
            모델을 선택해주세요.
          </p>
        </div>
      )}

      {/* 입력 폼 */}
      <form onSubmit={handleSubmit} className="flex items-end gap-3">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              disabled 
                ? "모델을 선택해주세요..." 
                : "메시지를 입력하세요... (Shift+Enter로 줄바꿈)"
            }
            disabled={disabled || isLoading}
            className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            rows={1}
            maxLength={4000}
          />
          <div className="absolute bottom-2 right-2 text-xs text-gray-400">
            {message.length}/4000
          </div>
        </div>

        {/* 버튼들 */}
        <div className="flex gap-2">
          {isLoading ? (
            <button
              type="button"
              onClick={onStopChat}
              className="px-4 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors"
              title="생성 중단"
            >
              <StopCircle className="w-5 h-5" />
            </button>
          ) : (
            <button
              type="submit"
              disabled={!message.trim() || disabled}
              className="px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              title="메시지 전송"
            >
              <Send className="w-5 h-5" />
            </button>
          )}

          <button
            type="button"
            onClick={handleClearChat}
            disabled={disabled}
            className="px-4 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            title="대화 초기화"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
        </div>
      </form>

      {/* 도움말 */}
      <div className="mt-3 text-xs text-gray-500">
        <p>💡 팁: Enter로 전송, Shift+Enter로 줄바꿈</p>
      </div>
    </div>
  );
};

export default MessageInput;
