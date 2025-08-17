import { useState } from 'react'
import ModelSelector from './components/ModelSelector'
import './App.css'

function App() {
  const [selectedModel, setSelectedModel] = useState<string>('')

  const handleModelChange = (profileId: string) => {
    setSelectedModel(profileId)
    console.log('Selected model:', profileId)
  }

  return (
    <div className="App">
      <div className="container mx-auto p-4">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            vLLM Chat Assistant
          </h1>
          <p className="text-gray-600">
            AI 모델을 선택하고 대화를 시작하세요
          </p>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* 모델 선택 패널 */}
          <div className="lg:col-span-1">
            <ModelSelector onModelChange={handleModelChange} />
          </div>

          {/* 채팅 영역 */}
          <div className="lg:col-span-2">
            <div className="bg-white border rounded-lg shadow-sm p-6 min-h-[400px]">
              <div className="text-center text-gray-500">
                {selectedModel ? (
                  <div>
                    <p className="mb-2">선택된 모델:</p>
                    <code className="bg-gray-100 px-2 py-1 rounded">
                      {selectedModel}
                    </code>
                    <p className="mt-4">채팅 기능은 곧 추가될 예정입니다.</p>
                  </div>
                ) : (
                  <p>모델을 선택해주세요.</p>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
