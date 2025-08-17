import React, { useRef, useEffect } from 'react';
import { Message as MessageType } from '../types/chat';
import Message from './Message';
import MessageInput from './MessageInput';

interface ChatAreaProps {
  messages: MessageType[];
  isLoading: boolean;
  selectedModel: string | null;
  onSendMessage: (message: string) => void;
  onStopChat: () => void;
  onClearChat: () => void;
}

const ChatArea: React.FC<ChatAreaProps> = ({
  messages,
  isLoading,
  selectedModel,
  onSendMessage,
  onStopChat,
  onClearChat,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 새 메시지가 추가될 때 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const isDisabled = !selectedModel;

  return (
    <div className="flex flex-col h-full bg-white rounded-lg border shadow-sm">
      {/* 헤더 */}
      <div className="p-4 bg-white border-b rounded-t-lg flex-shrink-0">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">채팅</h3>
            {selectedModel && (
              <p className="text-sm text-gray-600">
                현재 모델: <span className="font-medium">{selectedModel}</span>
              </p>
            )}
          </div>
          
          {messages.length > 0 && (
            <div className="text-sm text-gray-500">
              {messages.length}개 메시지
            </div>
          )}
        </div>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-12">
            {isDisabled ? (
              <div className="text-gray-500">
                <div className="text-4xl mb-4">🤖</div>
                <h3 className="text-lg font-medium mb-2">모델을 선택해주세요</h3>
                <p className="text-sm">왼쪽에서 사용할 AI 모델을 선택하면 채팅을 시작할 수 있습니다.</p>
              </div>
            ) : (
              <div className="text-gray-500">
                <div className="text-4xl mb-4">💬</div>
                <h3 className="text-lg font-medium mb-2">대화를 시작해보세요</h3>
                <p className="text-sm">아래 입력창에 메시지를 입력하고 AI와 대화해보세요.</p>
              </div>
            )}
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <Message
                key={message.id}
                message={message}
                isStreaming={isLoading && message.role === 'assistant' && message.content === ''}
              />
            ))}
            
            {/* 로딩 표시 */}
            {isLoading && (
              <div className="flex items-center justify-center py-4">
                <div className="flex items-center space-x-2 text-gray-500">
                  <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  <span className="text-sm">AI가 응답을 생성하고 있습니다...</span>
                </div>
              </div>
            )}
          </>
        )}
        
        {/* 자동 스크롤을 위한 참조 요소 */}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <MessageInput
        onSendMessage={onSendMessage}
        onStopChat={onStopChat}
        onClearChat={onClearChat}
        isLoading={isLoading}
        disabled={isDisabled}
      />
    </div>
  );
};

export default ChatArea;
