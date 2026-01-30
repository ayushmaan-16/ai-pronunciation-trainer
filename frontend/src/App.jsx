import { useState, useEffect } from 'react';
import { useReactMediaRecorder } from 'react-media-recorder';
import axios from 'axios';
import { Mic, Square, RefreshCw } from 'lucide-react';
import './App.css';

const App = () => {
  const [sentence, setSentence] = useState("");
  const [score, setScore] = useState(null);
  const [breakdown, setBreakdown] = useState([]); 
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);

  const fetchSentence = async () => {
    try {
      setScore(null);
      setBreakdown([]); 
      setAudioUrl(null);
      const response = await axios.get('http://127.0.0.1:8000/get-sentence');
      setSentence(response.data.text);
    } catch (error) {
      console.error("Error fetching sentence:", error);
    }
  };

  useEffect(() => {
    fetchSentence();
  }, []);

  const { status, startRecording, stopRecording } = useReactMediaRecorder({
    audio: true,
    onStop: (blobUrl, blob) => {
      setAudioUrl(blobUrl); 
      handleUpload(blob);
    }
  });

  const handleUpload = async (audioBlob) => {
    setLoading(true);
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.wav");
    formData.append("text", sentence); 

    try {
      const response = await axios.post('http://127.0.0.1:8000/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // --- DEBUGGING & SAFETY CHECK ---
      console.log("Backend Response:", response.data);

      if (response.data.error) {
        alert("Backend Error: " + response.data.error); // Show the real error!
        return;
      }

      setScore(response.data.score);
      // Safety: Ensure breakdown is an array, fallback to empty list
      setBreakdown(response.data.breakdown || []); 

    } catch (error) {
      console.error("Error uploading audio:", error);
      alert("Network Error: Could not reach backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>🗣️ AI Pronunciation Trainer</h1>
      
      <div className="card">
        <h2>Read this aloud:</h2>
        <p className="sentence">"{sentence}"</p>
        <button onClick={fetchSentence} className="refresh-btn">
          <RefreshCw size={16} /> New Sentence
        </button>
      </div>

      <div className="controls">
        {status !== 'recording' ? (
          <button onClick={startRecording} className="record-btn">
            <Mic /> Start Recording
          </button>
        ) : (
          <button onClick={stopRecording} className="stop-btn">
            <Square /> Stop & Analyze
          </button>
        )}
      </div>

      {audioUrl && (
        <div className="audio-preview">
          <audio src={audioUrl} controls />
        </div>
      )}

      {loading && <p className="loading">⏳ Analyzing your voice...</p>}

      {/* SAFETY CHECK: Only render if score exists */}
      {score !== null && (
        <div className="result-card">
          <h3>Overall Score: {score}%</h3>
          
          <div className="word-breakdown">
            {/* SAFETY CHECK: Use optional chaining (?.) to prevent crashes */}
            {breakdown?.map((item, index) => (
              <span 
                key={index} 
                className={`word-badge ${item.accuracy > 80 ? 'green' : 'red'}`}
                title={`Accuracy: ${item.accuracy}%`}
              >
                {item.word}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default App;