import { SavedPattern } from './types';

export const RULE_PRESETS: Record<string, { birth: number[]; survive: number[] }> = {
  "Conway's Life (B3/S23)": { birth: [3], survive: [2, 3] },
  "HighLife (B36/S23)": { birth: [3, 6], survive: [2, 3] },
  "Day & Night (B3678/S34678)": { birth: [3, 6, 7, 8], survive: [3, 4, 6, 7, 8] },
  "Seeds (B2/S)": { birth: [2], survive: [] },
  "Life without Death (B3/S012345678)": { birth: [3], survive: [0, 1, 2, 3, 4, 5, 6, 7, 8] },
  "Replicator (B1357/S1357)": { birth: [1, 3, 5, 7], survive: [1, 3, 5, 7] },
  "Maze (B3/S12345)": { birth: [3], survive: [1, 2, 3, 4, 5] },
};

export class LifeGrid {
  rows: number;
  cols: number;
  wrap: boolean;
  birth: Set<number>;
  survive: Set<number>;
  cells: Uint8Array;
  generation: number;

  constructor(
    rows: number,
    cols: number,
    wrap: boolean = true,
    birth: Iterable<number> = [3],
    survive: Iterable<number> = [2, 3]
  ) {
    this.rows = Math.max(1, rows);
    this.cols = Math.max(1, cols);
    this.wrap = wrap;
    this.birth = new Set(birth);
    this.survive = new Set(survive);
    this.cells = new Uint8Array(this.rows * this.cols);
    this.generation = 0;
  }

  private idx(r: number, c: number): number {
    return r * this.cols + c;
  }

  resize(newRows: number, newCols: number): void {
    newRows = Math.max(1, newRows);
    newCols = Math.max(1, newCols);
    if (newRows === this.rows && newCols === this.cols) return;

    const newCells = new Uint8Array(newRows * newCols);
    const minR = Math.min(newRows, this.rows);
    const minC = Math.min(newCols, this.cols);

    for (let r = 0; r < minR; r++) {
      for (let c = 0; c < minC; c++) {
        newCells[r * newCols + c] = this.cells[r * this.cols + c];
      }
    }

    this.cells = newCells;
    this.rows = newRows;
    this.cols = newCols;
  }

  clear(): void {
    this.cells.fill(0);
    this.generation = 0;
  }

  randomize(density: number): void {
    const total = this.rows * this.cols;
    for (let i = 0; i < total; i++) {
      this.cells[i] = Math.random() < density ? 1 : 0;
    }
    this.generation = 0;
  }

  toggleCell(row: number, col: number): number {
    if (row >= 0 && row < this.rows && col >= 0 && col < this.cols) {
      const index = this.idx(row, col);
      this.cells[index] = this.cells[index] ? 0 : 1;
      return this.cells[index];
    }
    return 0;
  }

  setCell(row: number, col: number, value: number): void {
    if (row >= 0 && row < this.rows && col >= 0 && col < this.cols) {
      this.cells[this.idx(row, col)] = value ? 1 : 0;
    }
  }

  getCell(row: number, col: number): number {
    if (row >= 0 && row < this.rows && col >= 0 && col < this.cols) {
      return this.cells[this.idx(row, col)];
    }
    return 0;
  }

  population(): number {
    let count = 0;
    const len = this.cells.length;
    for (let i = 0; i < len; i++) {
      if (this.cells[i] === 1) count++;
    }
    return count;
  }

  step(): void {
    const rows = this.rows;
    const cols = this.cols;
    const total = rows * cols;
    const nextCells = new Uint8Array(total);
    const wrap = this.wrap;
    const current = this.cells;

    for (let r = 0; r < rows; r++) {
      const rOffset = r * cols;

      // Pre-compute neighbor row indices
      let rPrev = r - 1;
      let rNext = r + 1;
      if (wrap) {
        if (rPrev < 0) rPrev = rows - 1;
        if (rNext >= rows) rNext = 0;
      }
      const rPrevOffset = rPrev >= 0 ? rPrev * cols : -1;
      const rNextOffset = rNext < rows ? rNext * cols : -1;

      for (let c = 0; c < cols; c++) {
        let cPrev = c - 1;
        let cNext = c + 1;
        if (wrap) {
          if (cPrev < 0) cPrev = cols - 1;
          if (cNext >= cols) cNext = 0;
        }

        let neighbors = 0;

        // Top 3 neighbors
        if (rPrevOffset !== -1) {
          if (cPrev >= 0 && current[rPrevOffset + cPrev]) neighbors++;
          if (current[rPrevOffset + c]) neighbors++;
          if (cNext < cols && current[rPrevOffset + cNext]) neighbors++;
        }

        // Left & Right
        if (cPrev >= 0 && current[rOffset + cPrev]) neighbors++;
        if (cNext < cols && current[rOffset + cNext]) neighbors++;

        // Bottom 3 neighbors
        if (rNextOffset !== -1) {
          if (cPrev >= 0 && current[rNextOffset + cPrev]) neighbors++;
          if (current[rNextOffset + c]) neighbors++;
          if (cNext < cols && current[rNextOffset + cNext]) neighbors++;
        }

        const isAlive = current[rOffset + c] === 1;
        const curIdx = rOffset + c;

        if (isAlive) {
          if (this.survive.has(neighbors)) {
            nextCells[curIdx] = 1;
          }
        } else {
          if (this.birth.has(neighbors)) {
            nextCells[curIdx] = 1;
          }
        }
      }
    }

    this.cells = nextCells;
    this.generation++;
  }

  toDict(cellSize?: number): SavedPattern {
    const alive: [number, number][] = [];
    for (let r = 0; r < this.rows; r++) {
      for (let c = 0; c < this.cols; c++) {
        if (this.cells[this.idx(r, c)] === 1) {
          alive.push([r, c]);
        }
      }
    }

    return {
      rows: this.rows,
      cols: this.cols,
      wrap: this.wrap,
      birth: Array.from(this.birth).sort((a, b) => a - b),
      survive: Array.from(this.survive).sort((a, b) => a - b),
      generation: this.generation,
      cell_size: cellSize,
      alive_cells: alive,
    };
  }

  static fromDict(d: SavedPattern): LifeGrid {
    const grid = new LifeGrid(
      d.rows,
      d.cols,
      d.wrap ?? true,
      d.birth ?? [3],
      d.survive ?? [2, 3]
    );

    if (Array.isArray(d.alive_cells)) {
      for (const [r, c] of d.alive_cells) {
        grid.setCell(r, c, 1);
      }
    }

    grid.generation = d.generation ?? 0;
    return grid;
  }
}
