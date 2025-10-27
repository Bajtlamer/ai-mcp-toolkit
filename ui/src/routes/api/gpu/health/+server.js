import { json } from '@sveltejs/kit';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/** @type {import('./$types').RequestHandler} */
export async function GET({ cookies }) {
	let gpuName = 'Unknown';
	let gpuAvailable = false;
	let gpuBackend = 'auto';
	let ollamaModel = 'None';
	let ollamaMemory = '0 MB';
	let ollamaAccelerated = false;

	try {
		// Check GPU_BACKEND environment variable
		const configuredBackend = process.env.GPU_BACKEND || 'auto';
		gpuBackend = configuredBackend;
		
		if (configuredBackend === 'cuda' || configuredBackend === 'auto') {
			// Try nvidia-smi (CUDA/NVIDIA GPU)
			try {
				const { stdout: nvidiaOutput } = await execAsync(
					'nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits'
				);
				
				const gpuData = nvidiaOutput.trim().split(', ');
				if (gpuData.length >= 5) {
					const [name, utilization, memoryUsed, memoryTotal, temperature] = gpuData;
					gpuName = name.trim();
					gpuBackend = 'cuda';
					gpuAvailable = true;
				}
			} catch (nvidiaError) {
				if (configuredBackend === 'cuda') {
					// CUDA explicitly requested but not available
					gpuName = 'CUDA Not Available';
					gpuBackend = 'cuda';
					gpuAvailable = false;
				}
			}
		}
		
		if (!gpuAvailable && (configuredBackend === 'metal' || configuredBackend === 'auto')) {
			// Check for macOS Metal
			try {
				const { stdout: systemInfo } = await execAsync('system_profiler SPDisplaysDataType');
				if (systemInfo.includes('Metal') || systemInfo.includes('Apple')) {
					gpuName = 'Apple Silicon (Metal)';
					gpuBackend = 'metal';
					gpuAvailable = true;
				}
			} catch (macError) {
				if (configuredBackend === 'metal') {
					// Metal explicitly requested but not available
					gpuName = 'Metal Not Available';
					gpuBackend = 'metal';
					gpuAvailable = false;
				}
			}
		}
		
		if (configuredBackend === 'cpu') {
			gpuName = 'CPU Only (Configured)';
			gpuBackend = 'cpu';
			gpuAvailable = false;
		}
		
		if (!gpuAvailable && configuredBackend === 'auto') {
			// Auto mode: neither CUDA nor Metal detected
			gpuName = 'CPU Only';
			gpuBackend = 'cpu';
		}

		// Get Ollama model info from backend /gpu/health endpoint
		try {
			const sessionId = cookies.get('session_id');
			const ollamaResponse = await fetch('http://localhost:8000/gpu/health', {
				headers: sessionId ? {
					'Cookie': `session_id=${sessionId}`
				} : {}
			});
			if (ollamaResponse.ok) {
				const ollamaData = await ollamaResponse.json();
				if (ollamaData.ollama_model && ollamaData.ollama_model !== 'None') {
					ollamaModel = ollamaData.ollama_model;
					ollamaMemory = ollamaData.ollama_memory_usage || '0 MB';
					ollamaAccelerated = ollamaData.ollama_gpu_accelerated || false;
				}
			}
		} catch (ollamaError) {
			// Silently fail - GPU health may require auth or Ollama may not be running
			console.debug('Could not get Ollama info from backend:', ollamaError.message);
		}

		// If Ollama is running, consider GPU available even without nvidia-smi
		if (ollamaModel !== 'None' && !gpuAvailable) {
			gpuAvailable = true;
		}

		// Get configured model from backend API
		let configuredModel = 'Unknown';
		try {
			const backendResponse = await fetch('http://localhost:8000/model/current');
			if (backendResponse.ok) {
				const data = await backendResponse.json();
				if (data.model) {
					configuredModel = data.model;
				}
			}
		} catch (e) {
			// Fallback to env variable
			configuredModel = process.env.OLLAMA_MODEL || 'Unknown';
		}
		
		// If no model is currently loaded, show configured model
		if (ollamaModel === 'None') {
			ollamaModel = configuredModel + ' (configured)';
		}
		
		return json({
			gpu_available: gpuAvailable,
			gpu_name: gpuName,
			gpu_backend: gpuBackend,
			gpu_utilization: 0, // Not available on macOS without specific tooling
			gpu_memory_usage: 'N/A',
			gpu_temperature: 0,
			ollama_gpu_accelerated: ollamaAccelerated,
			ollama_model: ollamaModel,
			ollama_model_configured: configuredModel,
			ollama_memory_usage: ollamaMemory
		}, {
			headers: {
				'Cache-Control': 'no-cache, no-store, must-revalidate',
				'Pragma': 'no-cache',
				'Expires': '0'
			}
		});
		
	} catch (error) {
		console.error('GPU health API error:', error);
		
		// Fallback
		return json({
			gpu_available: false,
			gpu_name: 'Unknown',
			gpu_backend: 'unknown',
			gpu_utilization: 0,
			gpu_memory_usage: 'N/A',
			gpu_temperature: 0,
			ollama_gpu_accelerated: false,
			ollama_model: 'None',
			ollama_memory_usage: '0 MB',
			error: error.message
		}, {
			status: 200,
			headers: {
				'Cache-Control': 'no-cache, no-store, must-revalidate',
				'Pragma': 'no-cache',
				'Expires': '0'
			}
		});
	}
}
