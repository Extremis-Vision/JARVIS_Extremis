import { useState, useEffect, useRef } from 'react';

const AudioVisualizer = () => {
  const [isListening, setIsListening] = useState(false);
  const [sensitivity, setSensitivity] = useState(5);
  const [error, setError] = useState<string | null>(null);
  
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animationRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Initialize audio context
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    analyserRef.current = audioContextRef.current.createAnalyser();
    analyserRef.current.fftSize = 256;
    
    return () => {
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Start/stop microphone access
  useEffect(() => {
    if (isListening) {
      startMicrophone();
    } else {
      stopMicrophone();
    }
  }, [isListening]);

  const startMicrophone = async () => {
    try {
      if (!audioContextRef.current) return;
      
      // Resume audio context if it's suspended
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
      sourceRef.current.connect(analyserRef.current!);
      
      // Start visualization
      visualize();
      setError(null);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setError('Could not access microphone. Please check permissions.');
      setIsListening(false);
    }
  };

  const stopMicrophone = () => {
    if (sourceRef.current) {
      sourceRef.current.disconnect();
      sourceRef.current = null;
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
      animationRef.current = null;
    }
    
    // Clear canvas
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        // Draw initial circle
        drawCircle(ctx, canvas.width / 2, canvas.height / 2, 100, 'rgb(59, 130, 246)');
      }
    }
  };

  const visualize = () => {
    if (!analyserRef.current || !canvasRef.current) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = 100;
    
    // Create data array for frequency data
    const bufferLength = analyserRef.current.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const draw = () => {
      animationRef.current = requestAnimationFrame(draw);
      
      analyserRef.current!.getByteFrequencyData(dataArray);
      
      // Clear canvas
      ctx.clearRect(0, 0, width, height);
      
      // Draw base circle
      drawCircle(ctx, centerX, centerY, radius, 'rgb(59, 130, 246)');
      
      // Draw wave around circle
      drawWave(ctx, centerX, centerY, radius, dataArray, sensitivity);
    };
    
    draw();
  };

  const drawCircle = (
    ctx: CanvasRenderingContext2D, 
    x: number, 
    y: number, 
    radius: number, 
    color: string
  ) => {
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();
  };

  const drawWave = (
    ctx: CanvasRenderingContext2D,
    centerX: number,
    centerY: number,
    radius: number,
    dataArray: Uint8Array,
    sensitivity: number
  ) => {
    const segments = 64; // Number of segments around the circle
    const angleStep = (2 * Math.PI) / segments;
    
    ctx.beginPath();
    
    for (let i = 0; i <= segments; i++) {
      const angle = i * angleStep;
      
      // Get frequency data for this segment
      const dataIndex = Math.floor((i / segments) * dataArray.length);
      const value = dataArray[dataIndex] / 255.0; // Normalize to 0-1
      
      // Calculate wave radius based on frequency data
      const waveRadius = radius + (value * sensitivity * 20);
      
      const x = centerX + Math.cos(angle) * waveRadius;
      const y = centerY + Math.sin(angle) * waveRadius;
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    
    ctx.closePath();
    
    // Create gradient
    const gradient = ctx.createRadialGradient(
      centerX, centerY, radius,
      centerX, centerY, radius + (100 * sensitivity / 5)
    );
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.8)');
    gradient.addColorStop(1, 'rgba(147, 51, 234, 0.2)');
    
    ctx.fillStyle = gradient;
    ctx.fill();
    
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.lineWidth = 2;
    ctx.stroke();
  };

  // Handle canvas resize
  useEffect(() => {
    const handleResize = () => {
      if (canvasRef.current) {
        const canvas = canvasRef.current;
        const container = canvas.parentElement;
        if (container) {
          canvas.width = container.clientWidth;
          canvas.height = container.clientHeight;
          
          // Redraw initial circle if not visualizing
          if (!isListening) {
            const ctx = canvas.getContext('2d');
            if (ctx) {
              ctx.clearRect(0, 0, canvas.width, canvas.height);
              drawCircle(ctx, canvas.width / 2, canvas.height / 2, 100, 'rgb(59, 130, 246)');
            }
          }
        }
      }
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [isListening]);

  // Draw initial circle
  useEffect(() => {
    if (canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        drawCircle(ctx, canvas.width / 2, canvas.height / 2, 100, 'rgb(59, 130, 246)');
      }
    }
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 p-4">
      <h1 className="text-3xl font-bold text-white mb-6">Audio Wave Visualizer</h1>
      
      {error && (
        <div className="bg-red-500 text-white p-4 rounded-lg mb-6 max-w-md">
          {error}
        </div>
      )}
      
      <div className="relative w-full max-w-2xl h-96 bg-gray-800 rounded-xl overflow-hidden mb-6">
        <canvas 
          ref={canvasRef} 
          className="w-full h-full"
        />
      </div>
      
      <div className="flex flex-col sm:flex-row gap-6 items-center">
        <button
          onClick={() => setIsListening(!isListening)}
          className={`px-6 py-3 rounded-lg font-medium text-white ${
            isListening 
              ? 'bg-red-500 hover:bg-red-600' 
              : 'bg-blue-500 hover:bg-blue-600'
          } transition-colors`}
        >
          {isListening ? 'Stop Microphone' : 'Start Microphone'}
        </button>
        
        <div className="flex flex-col items-center">
          <label htmlFor="sensitivity" className="text-white mb-2">
            Wave Sensitivity: {sensitivity}
          </label>
          <input
            id="sensitivity"
            type="range"
            min="1"
            max="10"
            step="1"
            value={sensitivity}
            onChange={(e) => setSensitivity(Number(e.target.value))}
            className="w-48"
          />
        </div>
      </div>
      
      <div className="mt-8 text-gray-400 text-center max-w-md">
        <p>Allow microphone access to see the visualization. The waves will respond to the sound frequency captured by your microphone.</p>
      </div>
    </div>
  );
};

export default AudioVisualizer;