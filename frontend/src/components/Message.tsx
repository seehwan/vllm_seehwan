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
    if (isUser) return <User className="w-6 h-6 text-blue-600 bg-blue-100 p-1 rounded-full" />;
    if (isAssistant) return <Bot className="w-6 h-6 text-green-600 bg-green-100 p-1 rounded-full" />;
    if (isSystem) return <AlertCircle className="w-6 h-6 text-yellow-600 bg-yellow-100 p-1 rounded-full" />;
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
      return 'bg-blue-100 border-blue-300 border-2 ml-12 shadow-md';
    }
    if (isAssistant) {
      return 'bg-green-100 border-green-300 border-2 mr-12 shadow-md';
    }
    if (isSystem) {
      return 'bg-yellow-100 border-yellow-300 border-2 mx-12 shadow-md';
    }
    return 'bg-gray-100 border-gray-300 border-2 mx-12 shadow-md';
  };

  const getTextStyle = () => {
    if (isUser) {
      return 'text-blue-900';
    }
    if (isAssistant) {
      return 'text-green-900';
    }
    if (isSystem) {
      return 'text-yellow-900';
    }
    return 'text-gray-900';
  };

  const getRoleStyle = () => {
    if (isUser) {
      return 'text-blue-700 font-semibold';
    }
    if (isAssistant) {
      return 'text-green-700 font-semibold';
    }
    if (isSystem) {
      return 'text-yellow-700 font-semibold';
    }
    return 'text-gray-700 font-semibold';
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
          <div className={`p-4 border rounded-xl shadow-lg ${getMessageStyle()}`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm ${getRoleStyle()}`}>
                {getRoleLabel()}
              </span>
              <span className="text-xs text-gray-500">
                {formatTime(message.timestamp)}
              </span>
            </div>
            
            <div className={`whitespace-pre-wrap ${getTextStyle()}`}>
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
