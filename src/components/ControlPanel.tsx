import React, { useRef } from 'react';
import { Play, Pause, StepForward, RotateCcw, Shuffle, Trash2, Download, Upload, ChevronDown } from 'lucide-react';
import { RULE_PRESETS } from '../life';

interface ControlPanelProps {
  speed: number;
  setSpeed: (v: number) => void;
  density: number;
  setDensity: (v: number) => void;
  cellSize: number;
  setCellSize: (v: number) => void;
  wrap: boolean;
  setWrap: (v: boolean) => void;
  showGridLines: boolean;
  setShowGridLines: (v: boolean) => void;
  birth: Set<number>;
  toggleBirth: (n: number) => void;
  survive: Set<number>;
  toggleSurvive: (n: number) => void;
  selectedPreset: string;
  onSelectPreset: (name: string) => void;
  isRunning: boolean;
  onTogglePlay: () => void;
  onStep: () => void;
  onResetGen: () => void;
  onRandomize: () => void;
  onClear: () => void;
  onSave: () => void;
  onLoadClick: () => void;
  generation: number;
  population: number;
  totalCells: number;
  cols: number;
  rows: number;
  statusMessage: string;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  speed,
  setSpeed,
  density,
  setDensity,
  cellSize,
  setCellSize,
  wrap,
  setWrap,
  showGridLines,
  setShowGridLines,
  birth,
  toggleBirth,
  survive,
  toggleSurvive,
  selectedPreset,
  onSelectPreset,
  isRunning,
  onTogglePlay,
  onStep,
  onResetGen,
  onRandomize,
  onClear,
  onSave,
  onLoadClick,
  generation,
  population,
  totalCells,
  cols,
  rows,
  statusMessage,
}) => {
  const [dropdownOpen, setDropdownOpen] = React.useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <aside
      id="control-panel"
      className="w-[340px] flex-shrink-0 h-full bg-[#1c1d23] border-l border-[#2e303a] p-5 overflow-y-auto flex flex-col gap-4.5 select-none text-sm text-[#e6e6eb] shadow-2xl z-10"
    >
      {/* Simulation Speed Slider */}
      <div id="speed-slider-group" className="flex flex-col gap-1.5">
        <div className="flex justify-between items-center text-xs font-medium text-[#d4d4dd]">
          <span>Speed (gen/sec)</span>
          <span className="text-[#5aaaff] font-mono font-semibold">{speed}</span>
        </div>
        <input
          id="speed-slider"
          type="range"
          min="1"
          max="60"
          step="1"
          value={speed}
          onChange={(e) => setSpeed(Number(e.target.value))}
          className="w-full h-2 bg-[#3c3e46] rounded-lg appearance-none cursor-pointer accent-[#5aaaff]"
        />
      </div>

      {/* Randomize Density Slider */}
      <div id="density-slider-group" className="flex flex-col gap-1.5">
        <div className="flex justify-between items-center text-xs font-medium text-[#d4d4dd]">
          <span>Randomize density (%)</span>
          <span className="text-[#5aaaff] font-mono font-semibold">{density}%</span>
        </div>
        <input
          id="density-slider"
          type="range"
          min="1"
          max="90"
          step="1"
          value={density}
          onChange={(e) => setDensity(Number(e.target.value))}
          className="w-full h-2 bg-[#3c3e46] rounded-lg appearance-none cursor-pointer accent-[#5aaaff]"
        />
      </div>

      {/* Cell Size Slider */}
      <div id="cellsize-slider-group" className="flex flex-col gap-1.5">
        <div className="flex justify-between items-center text-xs font-medium text-[#d4d4dd]">
          <span>Cell size (px)</span>
          <span className="text-[#5aaaff] font-mono font-semibold">{cellSize}px</span>
        </div>
        <input
          id="cellsize-slider"
          type="range"
          min="4"
          max="25"
          step="1"
          value={cellSize}
          onChange={(e) => setCellSize(Number(e.target.value))}
          className="w-full h-2 bg-[#3c3e46] rounded-lg appearance-none cursor-pointer accent-[#5aaaff]"
        />
      </div>

      <div className="h-px bg-[#2b2d37] my-0.5" />

      {/* Toggles */}
      <div className="flex flex-col gap-2.5">
        {/* Wrap Around */}
        <label id="wrap-toggle" className="flex items-center justify-between cursor-pointer group">
          <span className="text-xs font-medium text-[#d4d4dd] group-hover:text-white transition-colors">
            Wrap-around edges
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={wrap}
            onClick={() => setWrap(!wrap)}
            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              wrap ? 'bg-[#5aaaff]' : 'bg-[#464850]'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                wrap ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </button>
        </label>

        {/* Gridlines */}
        <label id="gridlines-toggle" className="flex items-center justify-between cursor-pointer group">
          <span className="text-xs font-medium text-[#d4d4dd] group-hover:text-white transition-colors">
            Show grid lines
          </span>
          <button
            type="button"
            role="switch"
            aria-checked={showGridLines}
            onClick={() => setShowGridLines(!showGridLines)}
            className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
              showGridLines ? 'bg-[#5aaaff]' : 'bg-[#464850]'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                showGridLines ? 'translate-x-4' : 'translate-x-0'
              }`}
            />
          </button>
        </label>
      </div>

      <div className="h-px bg-[#2b2d37] my-0.5" />

      {/* Birth Rule (B) */}
      <div id="birth-grid-group" className="flex flex-col gap-1.5">
        <span className="text-xs font-medium text-[#d4d4dd]">
          Birth (B) — neighbor counts
        </span>
        <div className="grid grid-cols-9 gap-1">
          {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((n) => {
            const active = birth.has(n);
            return (
              <button
                key={`b-${n}`}
                id={`birth-toggle-${n}`}
                type="button"
                onClick={() => toggleBirth(n)}
                className={`h-7 rounded text-xs font-bold transition-all ${
                  active
                    ? 'bg-[#5ad28c] text-[#121216] shadow-sm'
                    : 'bg-[#373940] text-[#a0a0a8] hover:bg-[#43454e] hover:text-white'
                }`}
              >
                {n}
              </button>
            );
          })}
        </div>
      </div>

      {/* Survive Rule (S) */}
      <div id="survive-grid-group" className="flex flex-col gap-1.5">
        <span className="text-xs font-medium text-[#d4d4dd]">
          Survive (S) — neighbor counts
        </span>
        <div className="grid grid-cols-9 gap-1">
          {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((n) => {
            const active = survive.has(n);
            return (
              <button
                key={`s-${n}`}
                id={`survive-toggle-${n}`}
                type="button"
                onClick={() => toggleSurvive(n)}
                className={`h-7 rounded text-xs font-bold transition-all ${
                  active
                    ? 'bg-[#5aaaff] text-[#121216] shadow-sm'
                    : 'bg-[#373940] text-[#a0a0a8] hover:bg-[#43454e] hover:text-white'
                }`}
              >
                {n}
              </button>
            );
          })}
        </div>
      </div>

      {/* Preset Dropdown */}
      <div id="preset-dropdown-group" ref={dropdownRef} className="relative flex flex-col gap-1.5">
        <span className="text-xs font-medium text-[#d4d4dd]">Rule preset</span>
        <button
          id="preset-dropdown-btn"
          type="button"
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="w-full flex items-center justify-between px-3 py-2 bg-[#2d2f36] border border-[#50525a] hover:border-[#70727c] rounded-md text-xs font-medium text-[#e6e6eb] transition-colors"
        >
          <span className="truncate">{selectedPreset}</span>
          <ChevronDown className={`w-3.5 h-3.5 text-[#a0a0a8] transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        {dropdownOpen && (
          <div className="absolute top-[58px] left-0 right-0 z-50 bg-[#28292f] border border-[#50525a] rounded-md shadow-xl overflow-hidden max-h-56 overflow-y-auto">
            {Object.keys(RULE_PRESETS).map((name) => {
              const isSelected = name === selectedPreset;
              return (
                <button
                  key={name}
                  type="button"
                  onClick={() => {
                    onSelectPreset(name);
                    setDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs transition-colors truncate block ${
                    isSelected
                      ? 'bg-[#3c6496] text-white font-semibold'
                      : 'text-[#d4d4dd] hover:bg-[#383a42] hover:text-white'
                  }`}
                >
                  {name}
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="h-px bg-[#2b2d37] my-0.5" />

      {/* Main Play / Pause Button */}
      <button
        id="play-pause-btn"
        type="button"
        onClick={onTogglePlay}
        className={`w-full py-2.5 px-4 rounded-md text-xs font-semibold flex items-center justify-center gap-2 shadow transition-all ${
          isRunning
            ? 'bg-[#c86446] hover:bg-[#db7252] text-white'
            : 'bg-[#3ca064] hover:bg-[#48b975] text-white'
        }`}
      >
        {isRunning ? (
          <>
            <Pause className="w-4 h-4" /> Pause (Space)
          </>
        ) : (
          <>
            <Play className="w-4 h-4" /> Play (Space)
          </>
        )}
      </button>

      {/* Action Buttons Row 1: Step, Reset Gen */}
      <div className="grid grid-cols-2 gap-2">
        <button
          id="step-btn"
          type="button"
          disabled={isRunning}
          onClick={onStep}
          className="py-2 px-2.5 bg-[#5064a0] hover:bg-[#5f75b8] disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition-colors shadow-sm"
        >
          <StepForward className="w-3.5 h-3.5" /> Step (S)
        </button>
        <button
          id="reset-gen-btn"
          type="button"
          onClick={onResetGen}
          className="py-2 px-2.5 bg-[#5a5a64] hover:bg-[#6b6b77] text-white rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition-colors shadow-sm"
        >
          <RotateCcw className="w-3.5 h-3.5" /> Reset gen #
        </button>
      </div>

      {/* Action Buttons Row 2: Randomize, Clear */}
      <div className="grid grid-cols-2 gap-2">
        <button
          id="randomize-btn"
          type="button"
          onClick={onRandomize}
          className="py-2 px-2.5 bg-[#96783c] hover:bg-[#b08d47] text-white rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition-colors shadow-sm"
        >
          <Shuffle className="w-3.5 h-3.5" /> Randomize (R)
        </button>
        <button
          id="clear-btn"
          type="button"
          onClick={onClear}
          className="py-2 px-2.5 bg-[#a04646] hover:bg-[#bb5353] text-white rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition-colors shadow-sm"
        >
          <Trash2 className="w-3.5 h-3.5" /> Clear (C)
        </button>
      </div>

      {/* Action Buttons Row 3: Save, Load */}
      <div className="grid grid-cols-2 gap-2">
        <button
          id="save-btn"
          type="button"
          onClick={onSave}
          className="py-2 px-2.5 bg-[#3c6e96] hover:bg-[#4982b1] text-white rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition-colors shadow-sm"
        >
          <Download className="w-3.5 h-3.5" /> Save (Ctrl+S)
        </button>
        <button
          id="load-btn"
          type="button"
          onClick={onLoadClick}
          className="py-2 px-2.5 bg-[#3c6e96] hover:bg-[#4982b1] text-white rounded-md text-xs font-medium flex items-center justify-center gap-1.5 transition-colors shadow-sm"
        >
          <Upload className="w-3.5 h-3.5" /> Load (Ctrl+O)
        </button>
      </div>

      {/* Stats and Status Readout */}
      <div id="stats-section" className="mt-auto pt-3 border-t border-[#2b2d37] flex flex-col gap-1 font-mono text-xs">
        <div className="text-[#f0f0f5] font-semibold text-sm">
          Generation: <span className="text-[#5aaaff]">{generation}</span>
        </div>
        <div className="text-[#b4c8dc]">
          Population: <span className="font-semibold">{population}</span> / {totalCells}
        </div>
        <div className="text-[#9696a0]">
          Grid: {cols} x {rows}
        </div>
        {statusMessage && (
          <div
            id="status-message"
            className="mt-1 px-2 py-1 bg-[#1a2e26] border border-[#2d5743] text-[#96e6b4] text-[11px] rounded transition-all animate-fade-in truncate font-sans"
          >
            {statusMessage}
          </div>
        )}
      </div>
    </aside>
  );
};
