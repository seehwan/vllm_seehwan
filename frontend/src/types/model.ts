export interface HardwareRequirements {
  min_vram_gb: number;
  recommended_vram_gb?: number;
  min_gpus?: number;
}

export interface ModelProfile {
  name: string;
  model_id: string;
  description: string;
  max_model_len: number;
  tensor_parallel_size: number;
  gpu_memory_utilization: number;
  dtype: string;
  swap_space: number;
  hardware_requirements?: HardwareRequirements;
}

export interface ModelStatus {
  current_profile: string | null;
  status: 'running' | 'switching' | 'stopped' | 'error';
  available_profiles: Record<string, ModelProfile>;
  message?: string;
}

export interface ModelSwitchRequest {
  profile_id: string;
}

export interface ModelSwitchResponse {
  success: boolean;
  message: string;
  current_profile?: string;
  switching_to?: string;
}
