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
      alert(`모델 전환을 시작했습니다: ${modelStatus?.available_profiles[profileId]?.name}`);
    } else {
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
      <div className="h-full bg-white border rounded-lg shadow-sm flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-500">모델 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-white border rounded-lg shadow-sm flex flex-col overflow-hidden">
      {/* 헤더 */}
      <div className="p-4 border-b bg-gray-50 flex-shrink-0">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">모델 선택</h3>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(modelStatus.status)}`}>
            {getStatusText(modelStatus.status)}
          </div>
        </div>
      </div>

      {/* 콘텐츠 영역 - 스크롤 가능 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* 현재 모델 정보 */}
        {modelStatus.current_profile && (
          <div className="p-3 bg-blue-50 rounded-md flex-shrink-0">
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

        {/* 모델 목록 */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            사용할 모델을 선택하세요:
          </label>
          
          {Object.entries(modelStatus.available_profiles || {}).map(([profileId, profile]) => (
            <div key={profileId} className="border rounded-lg overflow-hidden">
              <div
                className={`p-3 cursor-pointer transition-colors hover:bg-gray-50 ${
                  selectedProfile === profileId ? 'bg-blue-50 border-blue-200' : ''
                }`}
                onClick={() => setExpandedProfile(expandedProfile === profileId ? null : profileId)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium text-gray-900 truncate">{profile.name}</h4>
                      {selectedModel === profileId && (
                        <Check className="h-4 w-4 text-green-600 flex-shrink-0" />
                      )}
                      {modelStatus.current_profile === profileId && (
                        <div className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded flex-shrink-0">
                          현재
                        </div>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1 line-clamp-2">{profile.description}</p>
                  </div>
                  <ChevronDown 
                    className={`h-5 w-5 text-gray-400 transition-transform flex-shrink-0 ml-2 ${
                      expandedProfile === profileId ? 'rotate-180' : ''
                    }`} 
                  />
                </div>
              </div>

              {expandedProfile === profileId && (
                <div className="border-t bg-gray-50 p-3 space-y-2">
                  <div className="text-sm space-y-1">
                    <div><strong>모델 ID:</strong> {profile.model_id}</div>
                    <div><strong>최대 길이:</strong> {profile.max_model_len.toLocaleString()} 토큰</div>
                    <div><strong>GPU 병렬:</strong> {profile.tensor_parallel_size}</div>
                    <div><strong>메모리 사용률:</strong> {(profile.gpu_memory_utilization * 100).toFixed(0)}%</div>
                  </div>
                  
                  {profile.hardware_requirements && (
                    <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                      <div className="flex items-start space-x-1">
                        <Info className="h-3 w-3 text-yellow-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <div><strong>필요 VRAM:</strong> {profile.hardware_requirements.min_vram_gb}GB+</div>
                          {(profile.hardware_requirements.min_gpus || 0) > 1 && (
                            <div><strong>필요 GPU:</strong> {profile.hardware_requirements.min_gpus}개+</div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  <button
                    onClick={() => handleModelSwitch(profileId)}
                    disabled={switching || modelStatus.current_profile === profileId}
                    className={`w-full mt-3 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                      modelStatus.current_profile === profileId
                        ? 'bg-green-100 text-green-800 cursor-not-allowed'
                        : switching
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-blue-600 text-white hover:bg-blue-700'
                    }`}
                  >
                    {switching
                      ? '전환 중...'
                      : modelStatus.current_profile === profileId
                      ? '현재 사용 중'
                      : '이 모델로 전환'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* 전환 중 상태 */}
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

        {/* 상태 메시지 */}
        {modelStatus.message && (
          <div className="mt-2 text-sm text-gray-600">
            {modelStatus.message}
          </div>
        )}
      </div>
    </div>
  );
};

export default ModelSelector;
