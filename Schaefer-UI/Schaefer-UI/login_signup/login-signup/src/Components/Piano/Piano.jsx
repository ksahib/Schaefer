import { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'
import * as Tone from 'tone';
import { Midi } from "@tonejs/midi";
const piano_keys = 88;
const Notes = Array.from({ length: piano_keys }, (_, i) => 108 - i);
const note_height = 20;
const beat_width = 40;
const num_beats = 64;
const resizeMargin = 6;


function Piano() {
  const synth = useRef(null);
  const canvasref = useRef(null);
  const [notes, setNotes] = useState([]);
  const [bpm, setBpm] = useState(120);
  const [isPlaying, setIsplaying] = useState(false);
  const [dragInfo, setDragInfo] = useState(null);
  const requestRef = useRef();
  const playMarkerRef = useRef(0);
  const [markerMode, setMarkerMode] = useState(false);
  const [markers, setMarkers] = useState([]);
  const navigate = useNavigate()

  const getNoteLabel = (midi) => {
    const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    return noteNames[midi % 12] + Math.floor(midi / 12 - 1);
  };

  useEffect(() => {
    synth.current = new Tone.PolySynth().toDestination();
  }, []);

  const drawGrid = (ctx, playMarker = 0) => {
    ctx.clearRect(0, 0, canvasref.current.width, canvasref.current.height);

    Notes.forEach((note, i) => {
      const y = i * note_height;
      ctx.strokeStyle = note % 12 === 0 ? "#555" : "#ccc";
      ctx.beginPath();
      ctx.moveTo(40, y);
      ctx.lineTo(canvasref.current.width, y);
      ctx.stroke();

      ctx.fillStyle = "#333";
      ctx.font = "12px sans-serif";
      ctx.fillText(getNoteLabel(note), 5, y + 15);
    });

    for (let i = 0; i < num_beats; i++) {
      const x = 40 + i * beat_width;
      ctx.strokeStyle = i % 4 === 0 ? "#999" : "#eee";
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, piano_keys * note_height);
      ctx.stroke();
    }

    for (const note of notes) {
      const { pitch, start, duration } = note;
      const y = (108 - pitch) * note_height;
      const x = 40 + start * beat_width;
      const width = duration * beat_width;

      ctx.fillStyle = "#3b82f6";
      ctx.fillRect(x, y, width, note_height);
      ctx.fillStyle = "#1e3a8a";
      ctx.fillRect(x + width - resizeMargin, y, resizeMargin, note_height);
    }


    ctx.strokeStyle = "red";
    ctx.beginPath();
    ctx.moveTo(playMarker + 40, 0);
    ctx.lineTo(playMarker + 40, piano_keys * note_height);
    ctx.stroke();

    markers.forEach(({ beat, label }) => {
      const x = 40 + beat * beat_width;

      // Vertical line
      ctx.strokeStyle = "#10b981"; // emerald
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, piano_keys * note_height);
      ctx.stroke();

      // Text label
      ctx.fillStyle = "#065f46";
      ctx.font = "12px sans-serif";
      ctx.fillText(label, x + 2, 12);
    });
  };

  const animate = () => {
    const transportPos = Tone.Transport.seconds;
    const beatsPassed = transportPos / (60 / bpm);
    const newX = (beatsPassed * beat_width) % (num_beats * beat_width);
    playMarkerRef.current = newX;

    const ctx = canvasref.current.getContext("2d");
    drawGrid(ctx, newX);

    requestRef.current = requestAnimationFrame(animate);
  };

  const handlePlay = async () => {
    await Tone.start();
    await Tone.getContext().resume();

    Tone.Transport.stop();
    Tone.Transport.cancel();
    Tone.Transport.bpm.value = bpm;

    if (!isPlaying) {
      setIsplaying(true);


      notes.forEach(({ pitch, start, duration }) => {
        const noteName = getNoteLabel(pitch);
        const startTime = start * (60 / bpm);
        const durTime = duration * (60 / bpm);
        Tone.Transport.schedule((time) => {
          synth.current.triggerAttackRelease(noteName, durTime, time);
        }, startTime);
      });

      Tone.Transport.start("+0.1");
      requestRef.current = requestAnimationFrame(animate);
    } else {
      setIsplaying(false);
      cancelAnimationFrame(requestRef.current);
      playMarkerRef.current = 0;

      const ctx = canvasref.current.getContext("2d");
      drawGrid(ctx, 0);

      Tone.Transport.stop();
      Tone.Transport.cancel();
    }
  };

  useEffect(() => {
    const ctx = canvasref.current.getContext("2d");
    drawGrid(ctx);
  }, [notes]);

  const getNoteAt = (x, y) => {
    const beat = (x - 40) / beat_width;
    const pitch = 108 - Math.floor(y / note_height);

    for (let i = 0; i < notes.length; i++) {
      const note = notes[i];
      const noteX = 40 + note.start * beat_width;
      const noteY = (108 - note.pitch) * note_height;
      const width = note.duration * beat_width;

      if (
        y >= noteY &&
        y < noteY + note_height &&
        x >= noteX &&
        x < noteX + width
      ) {
        if (x >= noteX + width - resizeMargin) {
          return { index: i, type: 'resize' };
        }
        return { index: i, type: 'move', offsetX: x - noteX, offsetY: y - noteY };
      }
    }
    return null;
  };

  const handleMouseDown = async (e) => {
    await Tone.start();

    if (markerMode && e.button === 0) {
      const rect = canvasref.current.getBoundingClientRect();
      const x = e.clientX - rect.left;

      const beat = Math.floor((x - 40) / beat_width);

      if (beat >= 0 && beat < num_beats) {
        const label = prompt("Enter marker label (e.g. Verse, Chorus):");
        if (label) {
          setMarkers((prev) => [...prev, { beat, label }]);
        }
      }

      return;
    }

    const rect = canvasref.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const found = getNoteAt(x, y);

    if (e.button === 2) {

      if (found) {
        setNotes((prev) => {
          const updated = [...prev];
          updated.splice(found.index, 1);
          return updated;
        });
      }
      return;
    }

    if (found) {
      setDragInfo({ ...found, startX: x, startY: y });
    } else {
      const pitch = 108 - Math.floor(y / note_height);
      const start = Math.floor((x - 40) / beat_width);
      const duration = 1;
      const noteName = getNoteLabel(pitch);
      synth.current.triggerAttackRelease(noteName, "0.2s");
      setNotes((prev) => [...prev, { pitch, start, duration }]);
    }
  };



  const handleMouseMove = (e) => {
    if (!dragInfo) return;
    const rect = canvasref.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setNotes((prev) => {
      const updated = [...prev];
      const note = { ...updated[dragInfo.index] };

      if (dragInfo.type === 'move') {
        const newStart = Math.floor((x - dragInfo.offsetX - 40) / beat_width);
        const newPitch = 108 - Math.floor((y - dragInfo.offsetY) / note_height);
        note.start = Math.max(0, Math.min(num_beats - note.duration, newStart));
        note.pitch = Math.max(21, Math.min(108, newPitch));
      } else if (dragInfo.type === 'resize') {
        const deltaBeats = Math.max(1, Math.floor((x - dragInfo.startX) / beat_width));
        note.duration = Math.min(num_beats - note.start, deltaBeats);
      }

      updated[dragInfo.index] = note;
      return updated;
    });
  };

  const handleMouseUp = () => setDragInfo(null);

  const exportToJson = async () => {
    const beatsPerBar = 4;
    const sortedMarkers = [...markers].sort((a, b) => a.beat - b.beat);
    const enrichedMarkers = sortedMarkers.map((marker, i) => {
      const next = sortedMarkers[i + 1];
      const bars = next
        ? (next.beat - marker.beat) / beatsPerBar
        : (num_beats - marker.beat) / beatsPerBar;

      const start_bar = Math.floor(marker.beat / beatsPerBar);
      const end_bar = start_bar + Math.ceil(bars);

      return {
        ...marker,
        bars,
        start_bar,
        end_bar,
      };
    });

    const jsonData = { bpm, notes, markers: enrichedMarkers };

    // Send to FastAPI backend
    try {
      const response = await fetch("http://localhost:8000/analyse-midi-json/analyse-midi-json/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(jsonData),
      });

      if (!response.ok) {
        const error = await response.text();
        console.error("Server error:", error);
        alert("Error sending data to server.");
      } else {
        console.log("Data sent to server and inserted to MongoDB.");
        navigate('/Piano');
      }
    } catch (err) {
      console.error("Fetch error:", err);
      alert("Failed to connect to the backend.");
    }


    const blob = new Blob([JSON.stringify(jsonData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "composition.json";
    a.click();
    URL.revokeObjectURL(url);
  };





  return (
    <div className="p-4 font-sans">
      <div className="mb-4 flex items-center gap-4">
        <label className="flex items-center gap-2">
          <span className="text-sm font-medium">BPM:</span>
          <input
            type="number"
            className="border px-2 py-1 w-20 rounded"
            value={bpm}
            onChange={(e) => setBpm(Number(e.target.value))}
          />
        </label>
        <button
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1 rounded"
          onClick={handlePlay}
        >
          {isPlaying ? "Stop" : "Play"}
        </button>
        <button
          className={`px-4 py-1 rounded ${markerMode ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-800'}`}
          onClick={() => setMarkerMode((prev) => !prev)}
        >
          {markerMode ? "Exit Marker Mode" : "Add Marker"}
        </button>
        <button
          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-1 rounded"
          onClick={exportToJson}
        >
          Export
        </button>
        <p className="text-sm text-gray-500 ml-4">
          Left click = Add, Drag = Move/Resize, Right click = Delete, Click note = Play sound
        </p>
      </div>

      <div
        className="overflow-y-scroll border rounded shadow"
        style={{ height: "600px" }}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onContextMenu={(e) => e.preventDefault()}
      >
        <canvas
          ref={canvasref}
          width={beat_width * num_beats + 40}
          height={note_height * piano_keys}
          onMouseDown={handleMouseDown}
          style={{ background: "#f9fafb", display: "block" }}
        />
      </div>
    </div>
  );
}

export default Piano;
