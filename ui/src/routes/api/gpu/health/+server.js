import { json } from '@sveltejs/kit';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

/** @type {import('./$types').RequestHandler} */
export async function GET() {
	try {
		// Get real GPU data from nvidia-smi
		const { stdout: nvidiaOutput } = await execAsync(
			'nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits'
		);
		
		// Get Ollama model info
		let ollamaModel = 'None';
		let ollamaMemory = '0 MB';
		let ollamaAccelerated = false;
		
		try {
			const { stdout: ollamaPs } = await execAsync('ollama ps');
			const lines = ollamaPs.split('\n');
			if (lines.length > 1) {
				const modelLine = lines[1].trim();
				if (modelLine && modelLine !== '' && !modelLine.startsWith('NAME')) {
					const parts = modelLine.split(/\s+/);
					if (parts.length >= 4) {
						ollamaModel = parts[0];
						ollamaMemory = parts[2];
						ollamaAccelerated = parts[3].includes('GPU') || parts[3].includes('%');
					}
				}
			}
		} catch (ollamaError) {
			console.warn('Could not get Ollama info:', ollamaError.message);
		}
		
		const gpuData = nvidiaOutput.trim().split(', ');
		if (gpuData.length >= 5) {
			const [name, utilization, memoryUsed, memoryTotal, temperature] = gpuData;
			
			return json({
				gpu_available: true,
				gpu_name: name.trim(),
				gpu_utilization: parseInt(utilization) || 0,
				gpu_memory_usage: `${memoryUsed}/${memoryTotal} MB`,
				gpu_temperature: parseInt(temperature) || 0,
				ollama_gpu_accelerated: ollamaAccelerated,
				ollama_model: ollamaModel,
				ollama_memory_usage: ollamaMemory
			}, {
				headers: {
					'Cache-Control': 'no-cache, no-store, must-revalidate',
					'Pragma': 'no-cache',
					'Expires': '0'
				}
			});
		} else {
			throw new Error('Invalid nvidia-smi output');
		}
		
	} catch (error) {
		console.error('GPU health API error:', error);
		
		// Fallback: return error info
		return json({
			gpu_available: false,
			gpu_name: 'Unknown',
			gpu_utilization: 0,
			gpu_memory_usage: '0/0 MB',
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
