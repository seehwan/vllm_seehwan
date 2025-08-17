import React from 'react';
import { Message as MessageType } from '../types/chat';
import { User, Bot, AlertCircle } from 'lucide-react';

interface MessageProps {
  message: MessageType;
  isStreaming?: boolean;
}

const Message: React.FC<MessageProps> = ({ message, isStreaming = false }) => {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const isSystem = message.role === 'system';

  const getRoleIcon = () => {
    if (isUser) return <User className="w-5 h-5 text-blue-600" />;
    if (isAssistant) return <Bot className="w-5 h-5 text-green-600" />;
    if (isSystem) return <AlertCircle className="w-5 h-5 text-yellow-600" />;
    return null;
  };

  const getRoleLabel = () => {
    if (isUser) return '사용자';
    if (isAssistant) return 'AI 어시스턴트';
    if (isSystem) return '시스템';
    return '알 수 없음';
  };

  const getMessageStyle = () => {
    if (isUser) {
      return 'bg-blue-50 border-blue-200 ml-12';
    }
    if (isAssistant) {
      return 'bg-green-50 border-green-200 mr-12';
    }
    if (isSystem) {
      return 'bg-yellow-50 border-yellow-200 mx-12';
    }
    return 'bg-gray-50 border-gray-200 mx-12';
  };

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`mb-4 ${isUser ? 'text-right' : 'text-left'}`}>
      <div className="flex items-start gap-3">
        {!isUser && (
          <div className="flex-shrink-0">
            {getRoleIcon()}
          </div>
        )}
        
        <div className={`flex-1 ${isUser ? 'order-2' : 'order-1'}`}>
          <div className={`p-4 border rounded-lg shadow-sm ${getMessageStyle()}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                {getRoleLabel()}
              </span>
              <span className="text-xs text-gray-500">
                {formatTime(message.timestamp)}
              </span>
            </div>
            
            <div className="text-gray-800 whitespace-pre-wrap">
              {message.content}
              {isStreaming && isAssistant && (
                <span className="inline-block w-2 h-4 bg-green-500 ml-1 animate-pulse" />
              )}
            </div>
            
            {message.tokens && (
              <div className="mt-2 text-xs text-gray-500">
                토큰: {message.tokens}
              </div>
            )}
            
            {message.model && (
              <div className="mt-1 text-xs text-gray-400">
                모델: {message.model}
              </div>
            )}
          </div>
        </div>
        
        {isUser && (
          <div className="flex-shrink-0 order-1">
            {getRoleIcon()}
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;
