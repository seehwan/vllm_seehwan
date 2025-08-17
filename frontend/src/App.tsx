import { useEffect } from 'react'
import ModelSelector from './components/ModelSelector'
import ChatArea from './components/ChatArea'
import { useChat } from './hooks/useChat'
import { useModel } from './hooks/useModel'
import './App.css'

function App() {
  const { modelStatus } = useModel();
  const {
    messages,
    isLoading,
    selectedModel,
    sendMessage,
    stopChat,
    clearChat,
    setModel,
  } = useChat();

  const handleModelChange = (profileId: string) => {
    setModel(profileId);
  };

  // 모델 상태가 변경되면 채팅 모델도 업데이트
  useEffect(() => {
    if (modelStatus?.current_profile && !selectedModel) {
      setModel(modelStatus.current_profile);
    }
  }, [modelStatus?.current_profile, selectedModel, setModel]);

  return (
    <div className="App min-h-screen bg-gray-50">
      <div className="container mx-auto p-4 h-screen">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            vLLM Chat Assistant
          </h1>
          <p className="text-gray-600">
            AI 모델을 선택하고 대화를 시작하세요
          </p>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-120px)]">
          {/* 모델 선택 패널 */}
          <div className="lg:col-span-1 min-w-0">
            <ModelSelector 
              onModelChange={handleModelChange} 
              selectedModel={selectedModel}
            />
          </div>

          {/* 채팅 영역 */}
          <div className="lg:col-span-2 min-w-0">
            <ChatArea
              messages={messages}
              isLoading={isLoading}
              selectedModel={selectedModel}
              onSendMessage={sendMessage}
              onStopChat={stopChat}
              onClearChat={clearChat}
            />
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
