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
    <div className="App h-screen bg-gray-50 flex flex-col overflow-hidden">
      <div className="container mx-auto p-4 h-full flex flex-col">
        {/* 위쪽 - 타이틀 */}
        <header className="mb-6 flex-shrink-0">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            vLLM Chat Assistant
          </h1>
          <p className="text-gray-600">
            AI 모델을 선택하고 대화를 시작하세요
          </p>
        </header>

        {/* 아래쪽 - 좌우 분할 */}
        <main className="flex gap-6 flex-1 min-h-0 overflow-hidden">
          {/* 아래쪽-왼쪽 - 모델 선택 패널 */}
          <div className="w-80 flex-shrink-0 h-full overflow-hidden">
            <ModelSelector 
              onModelChange={handleModelChange} 
              selectedModel={selectedModel}
            />
          </div>

          {/* 아래쪽-오른쪽 - 채팅창 */}
          <div className="flex-1 h-full overflow-hidden">
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
