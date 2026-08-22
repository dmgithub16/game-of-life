import React, { useState, useRef, useEffect, useCallback } from 'react';
import { LifeGrid, RULE_PRESETS } from './life';
import { LifeCanvas } from './components/LifeCanvas';
import { ControlPanel } from './components/ControlPanel';
import { SavedPattern } from './types';

const DEFAULT_CELL_SIZE = 10;
const INITIAL_COLS = 70;
const INITIAL_ROWS = 70;

export const App: React.FC = () => {
  const [cellSize, setCellSizeState] = useState<number>(DEFAULT_CELL_SIZE);
  const [speed, setSpeed] = useState<number>(8);
  const [density, setDensity] = useState<number>(25);
  const [wrap, setWrapState] = useState<boolean>(true);
  const [showGridLines, setShowGridLines] = useState<boolean>(true);
  const [selectedPreset, setSelectedPreset] = useState<string>("Conway's Life (B3/S23)");
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [renderTrigger, setRenderTrigger] = useState<number>(0);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const statusTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // LifeGrid instance stored in ref to avoid recreating arrays on every render
  const gridRef = useRef<LifeGrid>(
    new LifeGrid(INITIAL_ROWS, INITIAL_COLS, true, [3], [2, 3])
  );

  // Initialize with random pattern
  useEffect(() => {
    gridRef.current.randomize(0.25);
    setRenderTrigger((t) => t + 1);
  }, []);

  const setStatus = useCallback((msg: string, durationMs: number = 3000) => {
    setStatusMessage(msg);
    if (statusTimeoutRef.current) {
      clearTimeout(statusTimeoutRef.current);
    }
    statusTimeoutRef.current = setTimeout(() => {
      setStatusMessage('');
    }, durationMs);
  }, []);

  // Update grid wrap property
  const setWrap = useCallback((newWrap: boolean) => {
    gridRef.current.wrap = newWrap;
    setWrapState(newWrap);
  }, []);

  // Grid resizing from canvas dimensions
  const handleResizeGrid = useCallback((newRows: number, newCols: number) => {
    gridRef.current.resize(newRows, newCols);
    setRenderTrigger((t) => t + 1);
  }, []);

  const handleCellSizeChange = useCallback((newSize: number) => {
    setCellSizeState(newSize);
    // Canvas ResizeObserver will automatically trigger handleResizeGrid with updated rows & cols
  }, []);

  const handleGridChange = useCallback(() => {
    setRenderTrigger((t) => t + 1);
  }, []);

  const handleTogglePlay = useCallback(() => {
    setIsRunning((prev) => !prev);
  }, []);

  const handleStep = useCallback(() => {
    gridRef.current.step();
    setRenderTrigger((t) => t + 1);
  }, []);

  const handleResetGen = useCallback(() => {
    gridRef.current.generation = 0;
    setRenderTrigger((t) => t + 1);
    setStatus('Reset generation count to 0');
  }, [setStatus]);

  const handleRandomize = useCallback(() => {
    gridRef.current.randomize(density / 100.0);
    setRenderTrigger((t) => t + 1);
    setStatus(`Randomized grid (${density}% density)`);
  }, [density, setStatus]);

  const handleClear = useCallback(() => {
    gridRef.current.clear();
    setRenderTrigger((t) => t + 1);
    setStatus('Cleared grid');
  }, [setStatus]);

  const toggleBirth = useCallback((n: number) => {
    const b = gridRef.current.birth;
    if (b.has(n)) {
      b.delete(n);
    } else {
      b.add(n);
    }
    setRenderTrigger((t) => t + 1);
  }, []);

  const toggleSurvive = useCallback((n: number) => {
    const s = gridRef.current.survive;
    if (s.has(n)) {
      s.delete(n);
    } else {
      s.add(n);
    }
    setRenderTrigger((t) => t + 1);
  }, []);

  const handleSelectPreset = useCallback((presetName: string) => {
    const preset = RULE_PRESETS[presetName];
    if (!preset) return;
    gridRef.current.birth = new Set(preset.birth);
    gridRef.current.survive = new Set(preset.survive);
    setSelectedPreset(presetName);
    setRenderTrigger((t) => t + 1);
    setStatus(`Preset applied: ${presetName}`);
  }, [setStatus]);

  // Save pattern to JSON file
  const handleSave = useCallback(() => {
    try {
      const data = gridRef.current.toDict(cellSize);
      const jsonStr = JSON.stringify(data, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const filename = `pattern-gen${gridRef.current.generation}-${Date.now()}.json`;

      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setStatus(`Saved: ${filename}`);
    } catch (err) {
      setStatus(`Save failed: ${err instanceof Error ? err.message : String(err)}`, 5000);
    }
  }, [cellSize, setStatus]);

  // Load pattern from JSON
  const processPatternData = useCallback((data: SavedPattern, filename: string) => {
    try {
      const loadedGrid = LifeGrid.fromDict(data);
      gridRef.current = loadedGrid;

      if (data.cell_size && data.cell_size >= 4 && data.cell_size <= 25) {
        setCellSizeState(data.cell_size);
      }
      if (typeof data.wrap === 'boolean') {
        setWrapState(data.wrap);
      }

      setIsRunning(false);
      setRenderTrigger((t) => t + 1);
      setStatus(`Loaded: ${filename}`);
    } catch (err) {
      setStatus(`Load failed: ${err instanceof Error ? err.message : String(err)}`, 5000);
    }
  }, [setStatus]);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const parsed = JSON.parse(text);
        processPatternData(parsed, file.name);
      } catch (err) {
        setStatus(`Invalid JSON file: ${err instanceof Error ? err.message : String(err)}`, 5000);
      }
    };
    reader.readAsText(file);
    // Clear input so same file can be selected again
    e.target.value = '';
  }, [processPatternData, setStatus]);

  const handleLoadClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is focusing an input or button
      if (['INPUT', 'SELECT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        return;
      }

      const ctrl = e.ctrlKey || e.metaKey;

      if (ctrl && e.key.toLowerCase() === 's') {
        e.preventDefault();
        handleSave();
      } else if (ctrl && e.key.toLowerCase() === 'o') {
        e.preventDefault();
        handleLoadClick();
      } else if (e.code === 'Space') {
        e.preventDefault();
        handleTogglePlay();
      } else if (e.key.toLowerCase() === 's' && !ctrl && !isRunning) {
        e.preventDefault();
        handleStep();
      } else if (e.key.toLowerCase() === 'r' && !ctrl) {
        e.preventDefault();
        handleRandomize();
      } else if (e.key.toLowerCase() === 'c' && !ctrl) {
        e.preventDefault();
        handleClear();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleSave, handleLoadClick, handleTogglePlay, handleStep, handleRandomize, handleClear, isRunning]);

  // Drag and drop JSON support
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.name.endsWith('.json')) {
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const parsed = JSON.parse(event.target?.result as string);
          processPatternData(parsed, file.name);
        } catch (err) {
          setStatus(`Failed to read file: ${err instanceof Error ? err.message : String(err)}`);
        }
      };
      reader.readAsText(file);
    }
  };

  // Main high-precision animation loop
  useEffect(() => {
    if (!isRunning) return;

    let animId: number;
    let lastTime = performance.now();
    let accumulator = 0;

    const loop = (currentTime: number) => {
      const dt = (currentTime - lastTime) / 1000;
      lastTime = currentTime;
      accumulator += dt;

      const stepInterval = 1.0 / Math.max(1, speed);

      let stepped = false;
      while (accumulator >= stepInterval) {
        gridRef.current.step();
        accumulator -= stepInterval;
        stepped = true;
      }

      if (stepped) {
        setRenderTrigger((t) => t + 1);
      }

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animId);
  }, [isRunning, speed]);

  const currentGrid = gridRef.current;

  return (
    <div
      id="app-root"
      className="flex h-screen w-screen overflow-hidden bg-[#121216]"
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {/* Hidden file input for loading patterns */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Main Grid Canvas Area */}
      <main id="main-content" className="flex-1 h-full overflow-hidden flex flex-col">
        <LifeCanvas
          grid={currentGrid}
          cellSize={cellSize}
          showGridLines={showGridLines}
          onGridChange={handleGridChange}
          onResizeGrid={handleResizeGrid}
          renderTrigger={renderTrigger}
        />
      </main>

      {/* Control Panel Docked Right */}
      <ControlPanel
        speed={speed}
        setSpeed={setSpeed}
        density={density}
        setDensity={setDensity}
        cellSize={cellSize}
        setCellSize={handleCellSizeChange}
        wrap={wrap}
        setWrap={setWrap}
        showGridLines={showGridLines}
        setShowGridLines={setShowGridLines}
        birth={currentGrid.birth}
        toggleBirth={toggleBirth}
        survive={currentGrid.survive}
        toggleSurvive={toggleSurvive}
        selectedPreset={selectedPreset}
        onSelectPreset={handleSelectPreset}
        isRunning={isRunning}
        onTogglePlay={handleTogglePlay}
        onStep={handleStep}
        onResetGen={handleResetGen}
        onRandomize={handleRandomize}
        onClear={handleClear}
        onSave={handleSave}
        onLoadClick={handleLoadClick}
        generation={currentGrid.generation}
        population={currentGrid.population()}
        totalCells={currentGrid.rows * currentGrid.cols}
        cols={currentGrid.cols}
        rows={currentGrid.rows}
        statusMessage={statusMessage}
      />
    </div>
  );
};
export default App;
