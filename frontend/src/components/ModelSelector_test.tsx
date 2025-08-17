import React from 'react';
import { useModel } from '../hooks/useModel';

interface ModelSelectorProps {
  onModelChange?: (profileId: string) => void;
  selectedModel: string | null;
}

const ModelSelector: React.FC<ModelSelectorProps> = ({ selectedModel }) => {
  const { modelStatus, switching } = useModel();

  console.log('ModelSelector - modelStatus:', modelStatus);
  console.log('ModelSelector - switching:', switching);

  return (
    <div className="bg-white rounded-lg shadow-md h-full p-4 border-2 border-red-300">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">모델 선택 (테스트)</h3>
      
      <div className="space-y-3">
        <div className="text-sm text-gray-600">
          디버깅 정보:
        </div>
        <div className="text-xs bg-gray-100 p-2 rounded">
          <div>modelStatus exists: {modelStatus ? 'YES' : 'NO'}</div>
          <div>switching: {switching ? 'YES' : 'NO'}</div>
          <div>selectedModel: {selectedModel || 'null'}</div>
        </div>
        
        {modelStatus ? (
          <div className="space-y-2">
            <div className="text-sm">
              <strong>현재 모델:</strong> {modelStatus.current_profile || 'None'}
            </div>
            <div className="text-sm">
              <strong>상태:</strong> {modelStatus.status || 'Unknown'}
            </div>
            <div className="text-sm">
              <strong>사용 가능한 모델 수:</strong> {Object.keys(modelStatus.available_profiles || {}).length}
            </div>
          </div>
        ) : (
          <div className="text-red-600">modelStatus가 null입니다</div>
        )}
      </div>
    </div>
  );
};

export default ModelSelector;
