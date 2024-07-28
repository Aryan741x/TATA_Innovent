'use client';
import { useState, useEffect } from 'react';
import io from 'socket.io-client';
import styles from './../../../styles/style.module.css';

const socket = io('http://localhost:5000');

export default function Home() {
  const [cameraStarted, setCameraStarted] = useState(false);
  const [classNames, setClassNames] = useState<string[]>([]);
  const [signInfo, setSignInfo] = useState<any[]>([]);
  const [mode, setMode] = useState<'traffic' | 'pothole' | 'both'>('traffic');
  const [cameraIndex, setCameraIndex] = useState<number>(0);
  const [availableCameras, setAvailableCameras] = useState<number[]>([]);

  useEffect(() => {
    const fetchCameras = async () => {
      const response = await fetch('http://localhost:5000/cameras');
      const data = await response.json();
      setAvailableCameras(data.cameras);
    };

    fetchCameras();
  }, []);

  const stopCamera = async () => {
    const response = await fetch('http://localhost:5000/stop_camera', { method: 'POST' });
    if (response.ok) {
      setCameraStarted(false);
    } else {
      console.log("Error stopping the Camera");
    }
  }

  const startCamera = async () => {
    setCameraStarted(true);
    let endpoint = 'http://localhost:5000/start_camera';
    if (mode === 'pothole') {
      endpoint = 'http://localhost:5000/start_camera_pothole';
    } else if (mode === 'both') {
      endpoint = 'http://localhost:5000/start_camera_both';
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ camera_index: cameraIndex })
    });
  };

  useEffect(() => {
    socket.on('connect', () => {
      console.log('Connected to the server');
    });

    socket.on('latest_result', async (data) => {
      if (data && data.result && data.result.predictions && data.result.predictions.length > 0) {
        const classes = data.result.predictions.map((prediction: { class: any; }) => prediction.class);
        setClassNames(classes);
        const response = await fetch('http://localhost:5000/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ signs: classes })
        });
        const signInfo = await response.json();
        setSignInfo(signInfo);
      }
      if (data.pothole !== undefined) {
        const potholeMessage = data.pothole ? 'Pothole detected' : 'No pothole detected';
        const potholeAction = data.pothole ? 'Slow down and avoid driving into it.' : 'Drive Carefully.';
        setSignInfo(prev => [
          ...prev,
          {
            sign: 'Pothole',
            details: potholeMessage,
            action: potholeAction
          }
        ]);
      }

    });

    return () => {
      socket.off('latest_result');
    };
  }, []);

  useEffect(() => {
    const fetchSignData = async () => {
      const response = await fetch('http://localhost:5000/signs');
      const data = await response.json();
      setSignInfo(data);
    };

    fetchSignData();
    const interval = setInterval(fetchSignData, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className={styles.container}>
      <h1 className={styles.h1}>Detection System</h1>
      <div className={styles.buttonGroup}>
        <button onClick={() => setMode('traffic')} disabled={cameraStarted} className={styles.button}>
          Traffic Signs
        </button>
        <button onClick={() => setMode('pothole')} disabled={cameraStarted} className={styles.button}>
          Potholes
        </button>
        <button onClick={() => setMode('both')} disabled={cameraStarted} className={styles.button}>
          Both
        </button>
      </div>
      <div>
        <label htmlFor="cameraSelect">Select Camera:</label>
        <select
          id="cameraSelect"
          value={cameraIndex}
          onChange={(e) => setCameraIndex(Number(e.target.value))}
        >
          {availableCameras.map((camera, index) => (
            <option key={index} value={camera}>
              Camera {camera}
            </option>
          ))}
        </select>
      </div>
      {cameraStarted ? (
        <button onClick={stopCamera} className={styles.button}>Stop Camera</button>
      ) : (
        <button onClick={startCamera} className={styles.button}>Start Camera</button>
      )}
      <div className={styles.detectionClasses}>
        <h2>Detection Classes:</h2>
        {classNames.length > 0 ? (
          <ul>
            {classNames.map((className, index) => (
              <li key={index}>{className}</li>
            ))}
          </ul>
        ) : (
          <p>No detection results</p>
        )}
      </div>
      <div className={styles.signInformation}>
        <h2 className={styles.h2}>Sign Information:</h2>
        {signInfo.length > 0 ? (
          <ul>
            {signInfo.map((info, index) => (
              <li key={index}>
                <strong>{info.sign}</strong>
                <div className={styles.signDetails}>Details: {info.details}</div>
                <div className={styles.signAction}>Action: {info.action}</div>
              </li>
            ))}
          </ul>
        ) : (
          <p>No sign information available</p>
        )}
      </div>
    </div>
  );
}
