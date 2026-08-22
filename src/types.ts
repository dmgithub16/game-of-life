export interface RulePreset {
  name: string;
  birth: number[];
  survive: number[];
}

export interface SavedPattern {
  rows: number;
  cols: number;
  wrap?: boolean;
  birth?: number[];
  survive?: number[];
  generation?: number;
  cell_size?: number;
  alive_cells: [number, number][];
}

export interface SimState {
  rows: number;
  cols: number;
  wrap: boolean;
  birth: Set<number>;
  survive: Set<number>;
  generation: number;
  cellSize: number;
  speed: number;
  density: number;
  showGridLines: boolean;
  isRunning: boolean;
  selectedPreset: string;
  statusMessage: string;
}
