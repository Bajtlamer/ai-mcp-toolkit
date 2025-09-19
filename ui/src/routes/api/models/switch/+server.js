import { json } from '@sveltejs/kit';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export async function POST({ request }) {
  try {
    const { model } = await request.json();
    
    if (!model) {
      return json({ success: false, error: 'Model name is required' }, { status: 400 });
    }

    // First, check if the model exists
    const { stdout: listOutput } = await execAsync('ollama list');
    const availableModels = listOutput.split('\n')
      .slice(1) // Skip header
      .map(line => line.split(/\s+/)[0])
      .filter(name => name && name !== '');

    if (!availableModels.includes(model)) {
      return json({ 
        success: false, 
        error: `Model '${model}' not found. Available models: ${availableModels.join(', ')}` 
      }, { status: 404 });
    }

    // Stop current models
    try {
      const { stdout: psOutput } = await execAsync('ollama ps');
      const lines = psOutput.split('\n');
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        // Skip empty lines and header line
        if (trimmedLine && !trimmedLine.startsWith('NAME') && !trimmedLine.includes('Done')) {
          const parts = trimmedLine.split(/\s+/);
          if (parts.length > 0 && parts[0]) {
            const modelName = parts[0];
            console.log(`Stopping model: ${modelName}`);
            await execAsync(`ollama stop "${modelName}"`);
          }
        }
      }
    } catch (error) {
      console.warn('Error stopping models:', error.message);
    }

    // Start the new model using a more direct approach
    // First try to preload it
    await execAsync(`ollama pull "${model}"`);
    
    // Then start it with a simple prompt
    const startCommand = `nohup bash -c 'echo "Hello" | ollama run "${model}" > /dev/null 2>&1' &`;
    await execAsync(startCommand);

    // Wait a bit longer for the model to fully load
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Verify the model is running with more lenient check
    let attempts = 0;
    let modelRunning = false;
    
    while (attempts < 15 && !modelRunning) {
      try {
        const { stdout: checkOutput } = await execAsync('ollama ps');
        modelRunning = checkOutput.includes(model);
        
        if (!modelRunning) {
          await new Promise(resolve => setTimeout(resolve, 2000));
          attempts++;
        }
      } catch (error) {
        attempts++;
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }

    if (modelRunning) {
      return json({ 
        success: true, 
        message: `Successfully switched to model: ${model}`,
        model: model
      });
    } else {
      return json({ 
        success: false, 
        error: `Model '${model}' failed to start properly` 
      }, { status: 500 });
    }

  } catch (error) {
    console.error('Model switch error:', error);
    return json({ 
      success: false, 
      error: `Failed to switch model: ${error.message}` 
    }, { status: 500 });
  }
}

export async function GET() {
  try {
    // Get available models
    const { stdout: listOutput } = await execAsync('ollama list');
    const models = listOutput.split('\n')
      .slice(1) // Skip header
      .map(line => {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 4 && parts[0]) {
          return {
            name: parts[0],
            id: parts[1],
            size: parts[2],
            modified: parts.slice(3).join(' ')
          };
        }
        return null;
      })
      .filter(Boolean);

    // Get currently running model
    let currentModel = null;
    try {
      const { stdout: psOutput } = await execAsync('ollama ps');
      const lines = psOutput.split('\n');
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        // Skip empty lines, header line, and shell output
        if (trimmedLine && !trimmedLine.startsWith('NAME') && !trimmedLine.includes('Done') && !trimmedLine.startsWith('[')) {
          const parts = trimmedLine.split(/\s+/);
          if (parts.length > 0 && parts[0]) {
            currentModel = parts[0];
            break; // Get the first running model
          }
        }
      }
    } catch (error) {
      console.warn('Error getting current model:', error.message);
    }

    return json({
      success: true,
      available: models,
      current: currentModel
    });
  } catch (error) {
    console.error('Error fetching models:', error);
    return json({ 
      success: false, 
      error: error.message 
    }, { status: 500 });
  }
}