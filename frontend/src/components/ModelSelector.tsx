import React, { useState } from 'react';
import { useModel } from '../hooks/useModel';
import { ChevronDown, Check, Info } from 'lucide-react';

interface ModelSelectorProps {
  onModelChange?: (profileId: string) => void;
  selectedModel: string | null;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ onModelChange, selectedModel }) => {
  const { modelStatus, switching, switchModel } = useModel();
  const [selectedProfile, setSelectedProfile] = useState<string>('');
  const [expandedProfile, setExpandedProfile] = useState<string | null>(null);

  const handleModelSwitch = async (profileId: string) => {
    const result = await switchModel(profileId);
    
    if (result.success) {
      setSelectedProfile(profileId);
      onModelChange?.(profileId);
      
      // 성공 알림
      alert(`모델 전환을 시작했습니다: ${modelStatus?.available_profiles[profileId]?.name}`);
    } else {
      // 실패 알림
      alert(`모델 전환 실패: ${result.message}`);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'text-green-600 bg-green-100';
      case 'switching':
        return 'text-yellow-600 bg-yellow-100';
      case 'stopped':
        return 'text-gray-600 bg-gray-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'running':
        return '실행 중';
      case 'switching':
        return '전환 중...';
      case 'stopped':
        return '정지됨';
      case 'error':
        return '오류';
      default:
        return '알 수 없음';
    }
  };

  if (!modelStatus) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <div className="animate-pulse">모델 정보를 불러오는 중...</div>
      </div>
    );
  }

  return (
    <div className="h-full bg-white border rounded-lg shadow-sm overflow-hidden">
      <div className="p-4 border-b bg-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">모델 선택</h3>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(modelStatus.status)}`}>
            {getStatusText(modelStatus.status)}
          </div>
        </div>

      {modelStatus.current_profile && (
        <div className="mb-4 p-3 bg-blue-50 rounded-md">
          <div className="text-sm font-medium text-blue-800">
            현재 모델: {modelStatus.available_profiles[modelStatus.current_profile]?.name}
          </div>
          <div className="text-xs text-blue-600 mt-1">
            {modelStatus.available_profiles[modelStatus.current_profile]?.description}
          </div>
          {selectedModel === modelStatus.current_profile && (
            <div className="mt-2 text-xs text-blue-600">
              ✅ 채팅에서 사용 중
            </div>
          )}
        </div>
      )}

      <div className="p-4 overflow-y-auto max-h-[calc(100vh-300px)]">
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            사용할 모델을 선택하세요:
          </label>
        
        {Object.entries(modelStatus.available_profiles).map(([profileId, profile]) => (
          <div
            key={profileId}
            className={`border rounded-md transition-colors ${
              modelStatus.current_profile === profileId
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
            }`}
          >
            <div
              className="p-3 cursor-pointer"
              onClick={() => {
                if (modelStatus.current_profile !== profileId && !switching) {
                  handleModelSwitch(profileId);
                }
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{profile.name}</div>
                  <div className="text-sm text-gray-600">{profile.description}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    모델 ID: {profile.model_id}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2">
                  {modelStatus.current_profile === profileId && (
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                      현재 사용 중
                    </span>
                  )}
                  
                  {switching && selectedProfile === profileId && (
                    <div className="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                  )}
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setExpandedProfile(expandedProfile === profileId ? null : profileId);
                    }}
                    className="p-1 hover:bg-gray-200 rounded transition-colors"
                  >
                    <ChevronDown 
                      className={`w-4 h-4 transition-transform ${
                        expandedProfile === profileId ? 'rotate-180' : ''
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>
            
            {/* 확장된 상세 정보 */}
            {expandedProfile === profileId && (
              <div className="px-3 pb-3 border-t border-gray-200 bg-gray-50">
                <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                  <div className="flex items-center space-x-1">
                    <Info className="w-3 h-3 text-gray-500" />
                    <span className="text-gray-600">최대 길이:</span>
                    <span className="font-medium">{profile.max_model_len.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Info className="w-3 h-3 text-gray-500" />
                    <span className="text-gray-600">GPU 병렬:</span>
                    <span className="font-medium">{profile.tensor_parallel_size}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Info className="w-3 h-3 text-gray-500" />
                    <span className="text-gray-600">메모리 사용:</span>
                    <span className="font-medium">{Math.round(profile.gpu_memory_utilization * 100)}%</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Info className="w-3 h-3 text-gray-500" />
                    <span className="text-gray-600">데이터 타입:</span>
                    <span className="font-medium">{profile.dtype}</span>
                  </div>
                </div>
                
                {/* 채팅에서 사용 버튼 */}
                {modelStatus.current_profile === profileId && selectedModel !== profileId && (
                  <button
                    onClick={() => onModelChange?.(profileId)}
                    className="mt-2 w-full px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                  >
                    채팅에서 사용
                  </button>
                )}
                
                {selectedModel === profileId && (
                  <div className="mt-2 text-xs text-green-600 bg-green-100 px-2 py-1 rounded text-center">
                    <Check className="w-3 h-3 inline mr-1" />
                    채팅에서 사용 중
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {modelStatus.status === 'switching' && (
        <div className="mt-4 p-3 bg-yellow-50 rounded-md">
          <div className="flex items-center">
            <div className="animate-spin h-4 w-4 border-2 border-yellow-500 border-t-transparent rounded-full mr-2"></div>
            <div className="text-sm text-yellow-800">
              모델을 전환하고 있습니다. 완료까지 1-3분 정도 소요됩니다.
            </div>
          </div>
        </div>
      )}

      {modelStatus.message && (
        <div className="mt-2 text-sm text-gray-600">
          {modelStatus.message}
        </div>
      )}
    </div>
  );
};

export default ModelSelector;
