import { useState, useEffect, useRef } from 'react';
import api, { API } from '../api';
import './VoiceInterface.css';



export default function VoiceInterface({ onTranscript, compact = false }) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [status, setStatus] = useState('idle');
  const [voiceStatus, setVoiceStatus] = useState({ stt: false, tts: false });
  const [recentCommands, setRecentCommands] = useState([]);
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    checkVoiceStatus();
    const interval = setInterval(checkVoiceStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isListening) {
      startAudioVisualization();
    } else {
      stopAudioVisualization();
    }
  }, [isListening]);

  const checkVoiceStatus = async () => {
    try {
      const res = await api.get(`/voice/status`);
      setVoiceStatus(res.data);
    } catch {
      setVoiceStatus({ stt: false, tts: false });
    }
  };

  const startListening = async () => {
    setIsListening(true);
    setStatus('listening');
    
    try {
      const res = await api.get(`/voice/listen`);
      const { transcription, available, error, command_recognized } = res.data;
      
      if (!available) {
        // Show the install hint in recent commands rather than crashing
        setRecentCommands(prev => [
          { text: `⚠️ ${error}`, time: new Date(), isError: true },
          ...prev
        ].slice(0, 5));
        setStatus('unavailable');
        setTimeout(() => setStatus('idle'), 3000);
        return;
      }
      
      if (command_recognized && transcription) {
        setRecentCommands(prev => [{ text: transcription, time: new Date() }, ...prev].slice(0, 5));
        onTranscript?.(transcription);
      }
    } catch (err) {
      console.error('Voice capture failed:', err);
      setStatus('error');
      setTimeout(() => setStatus('idle'), 2000);
    } finally {
      setIsListening(false);
      if (status !== 'unavailable' && status !== 'error') setStatus('idle');
    }
  };

  const speakText = async (text) => {
    if (!voiceStatus.tts) return;
    
    setIsSpeaking(true);
    setStatus('speaking');
    
    try {
      await api.post(`/voice/speak`, { 
        text: text.slice(0, 500), // Limit length
        engine: 'auto'
      });
    } catch (err) {
      console.error('TTS failed:', err);
    } finally {
      setIsSpeaking(false);
      setStatus('idle');
    }
  };

  const startAudioVisualization = async () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    try {
      // Initialize Web Audio API
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      audioCtxRef.current = audioCtx;
      
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      analyserRef.current = analyser;
      
      source.connect(analyser);
      
      const ctx = canvas.getContext('2d');
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const draw = () => {
        animationRef.current = requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArray);
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        const bars = 32;
        const barWidth = canvas.width / bars;
        
        for (let i = 0; i < bars; i++) {
          // Sample frequency bins evenly
          const binIndex = Math.floor((i / bars) * bufferLength);
          const value = dataArray[binIndex];
          const percent = value / 255;
          const barHeight = percent * canvas.height * 0.9;
          
          const x = i * barWidth;
          const y = canvas.height - barHeight;
          
          // Dynamic color based on frequency
          const hue = 200 + (i / bars) * 120; // Blue to purple to pink
          ctx.fillStyle = `hsla(${hue}, 80%, 60%, ${0.5 + percent * 0.5})`;
          ctx.fillRect(x, y, barWidth - 1, barHeight);
          
          // Glow effect for high energy
          if (percent > 0.7) {
            ctx.shadowColor = `hsla(${hue}, 80%, 60%, 0.8)`;
            ctx.shadowBlur = 10;
          } else {
            ctx.shadowBlur = 0;
          }
        }
      };
      
      draw();
    } catch (err) {
      console.error('Audio visualization failed:', err);
      // Fallback to idle animation
      startIdleAnimation();
    }
  };

  const startIdleAnimation = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let phase = 0;
    
    const animate = () => {
      if (!isListening) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const bars = 20;
      const barWidth = canvas.width / bars;
      
      for (let i = 0; i < bars; i++) {
        const height = Math.sin(phase + i * 0.5) * 15 + 20;
        const x = i * barWidth + barWidth * 0.1;
        const y = (canvas.height - height) / 2;
        
        ctx.fillStyle = `rgba(59, 130, 246, ${0.3 + Math.sin(phase + i) * 0.3})`;
        ctx.fillRect(x, y, barWidth * 0.8, height);
      }
      
      phase += 0.05;
      animationRef.current = requestAnimationFrame(animate);
    };
    
    animate();
  };

  const stopAudioVisualization = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close();
    }
    
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  };

  if (compact) {
    return (
      <div className="voice-interface-compact">
        <button 
          className={`voice-btn ${isListening ? 'listening' : ''} ${isSpeaking ? 'speaking' : ''}`}
          onClick={startListening}
          disabled={!voiceStatus.stt || isListening}
          title={voiceStatus.stt ? "Click to speak" : "Voice not available"}
        >
          {isListening ? '◉' : isSpeaking ? '◉' : '🎤'}
        </button>
        <canvas ref={canvasRef} width={60} height={40} className="voice-viz-compact" />
      </div>
    );
  }

  return (
    <div className="voice-interface">
      <div className="voice-header">
        <h3>Voice Commands</h3>
        <div className="voice-status">
          <span className={`status-indicator ${voiceStatus.stt ? 'on' : 'off'}`}>
            STT {voiceStatus.stt ? '●' : '○'}
          </span>
          <span className={`status-indicator ${voiceStatus.tts ? 'on' : 'off'}`}>
            TTS {voiceStatus.tts ? '●' : '○'}
          </span>
        </div>
      </div>

      <div className="voice-visualizer">
        <canvas 
          ref={canvasRef} 
          width={300} 
          height={100}
          className={`voice-canvas ${status}`}
        />
      </div>

      <div className="voice-controls">
        <button 
          className={`voice-main-btn ${isListening ? 'active' : ''}`}
          onClick={startListening}
          disabled={!voiceStatus.stt || isListening}
        >
          {isListening ? (
            <>
              <span className="pulse">◉</span>
              Listening...
            </>
          ) : (
            <>
              🎤 Hold to Speak
            </>
          )}
        </button>
        
        <div className="voice-presets">
          <button onClick={() => onTranscript?.("Work status")}>💼 Work</button>
          <button onClick={() => onTranscript?.("Fitness status")}>💪 Fitness</button>
          <button onClick={() => onTranscript?.("Mood check")}>🧠 Mood</button>
          <button onClick={() => onTranscript?.("What's on my agenda")}>📋 Tasks</button>
        </div>
      </div>

      {recentCommands.length > 0 && (
        <div className="recent-commands">
          <label>Recent</label>
          {recentCommands.map((cmd, i) => (
            <div key={i} className="command-item" onClick={() => onTranscript?.(cmd.text)}>
              <span>{cmd.text}</span>
              <time>{cmd.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>
            </div>
          ))}
        </div>
      )}

      <div className="voice-tips">
        <p>Try: "Log 45 minute strength workout" • "How am I feeling?" • "What should I focus on?"</p>
      </div>
    </div>
  );
}
