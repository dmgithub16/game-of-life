import React, { useRef, useEffect, useCallback } from 'react';
import { LifeGrid } from '../life';

interface LifeCanvasProps {
  grid: LifeGrid;
  cellSize: number;
  showGridLines: boolean;
  onGridChange: () => void;
  onResizeGrid: (rows: number, cols: number) => void;
  renderTrigger: number;
}

export const LifeCanvas: React.FC<LifeCanvasProps> = ({
  grid,
  cellSize,
  showGridLines,
  onGridChange,
  onResizeGrid,
  renderTrigger,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isPaintingRef = useRef(false);
  const paintValueRef = useRef(1);

  // ResizeObserver to calculate grid size from available container size
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          const cols = Math.max(1, Math.floor(width / cellSize));
          const rows = Math.max(1, Math.floor(height / cellSize));
          if (cols !== grid.cols || rows !== grid.rows) {
            onResizeGrid(rows, cols);
          }
        }
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  }, [cellSize, grid.cols, grid.rows, onResizeGrid]);

  // Render canvas
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = grid.cols * cellSize;
    const height = grid.rows * cellSize;

    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }

    // Clear background
    ctx.fillStyle = '#0a0a0d';
    ctx.fillRect(0, 0, width, height);

    // Draw live cells
    ctx.fillStyle = '#5ac8ff';
    const rows = grid.rows;
    const cols = grid.cols;
    const cells = grid.cells;

    for (let r = 0; r < rows; r++) {
      const rOffset = r * cols;
      for (let c = 0; c < cols; c++) {
        if (cells[rOffset + c] === 1) {
          ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
        }
      }
    }

    // Draw grid lines if enabled
    if (showGridLines && cellSize >= 4) {
      ctx.strokeStyle = '#23242a';
      ctx.lineWidth = 1;
      ctx.beginPath();

      // Vertical lines
      for (let x = 0; x <= width; x += cellSize) {
        ctx.moveTo(x + 0.5, 0);
        ctx.lineTo(x + 0.5, height);
      }

      // Horizontal lines
      for (let y = 0; y <= height; y += cellSize) {
        ctx.moveTo(0, y + 0.5);
        ctx.lineTo(width, y + 0.5);
      }

      ctx.stroke();
    }
  }, [grid, cellSize, showGridLines]);

  useEffect(() => {
    draw();
  }, [draw, renderTrigger]);

  const getCellCoords = (e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>): [number, number] | null => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    let clientX: number;
    let clientY: number;

    if ('touches' in e) {
      if (e.touches.length === 0) return null;
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = e.clientX;
      clientY = e.clientY;
    }

    const x = clientX - rect.left;
    const y = clientY - rect.top;

    if (x < 0 || x >= canvas.width || y < 0 || y >= canvas.height) {
      return null;
    }

    const col = Math.floor(x / cellSize);
    const row = Math.floor(y / cellSize);
    return [row, col];
  };

  const handlePointerDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (e.button !== 0) return; // Only left click
    const coords = getCellCoords(e);
    if (!coords) return;
    const [r, c] = coords;
    const currentVal = grid.getCell(r, c);
    const newVal = currentVal === 1 ? 0 : 1;
    paintValueRef.current = newVal;
    grid.setCell(r, c, newVal);
    isPaintingRef.current = true;
    onGridChange();
  };

  const handlePointerMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isPaintingRef.current) return;
    const coords = getCellCoords(e);
    if (!coords) return;
    const [r, c] = coords;
    if (grid.getCell(r, c) !== paintValueRef.current) {
      grid.setCell(r, c, paintValueRef.current);
      onGridChange();
    }
  };

  const handlePointerUp = () => {
    isPaintingRef.current = false;
  };

  const handleTouchStart = (e: React.TouchEvent<HTMLCanvasElement>) => {
    const coords = getCellCoords(e);
    if (!coords) return;
    const [r, c] = coords;
    const currentVal = grid.getCell(r, c);
    const newVal = currentVal === 1 ? 0 : 1;
    paintValueRef.current = newVal;
    grid.setCell(r, c, newVal);
    isPaintingRef.current = true;
    onGridChange();
  };

  const handleTouchMove = (e: React.TouchEvent<HTMLCanvasElement>) => {
    if (!isPaintingRef.current) return;
    const coords = getCellCoords(e);
    if (!coords) return;
    const [r, c] = coords;
    if (grid.getCell(r, c) !== paintValueRef.current) {
      grid.setCell(r, c, paintValueRef.current);
      onGridChange();
    }
  };

  return (
    <div
      id="life-canvas-container"
      ref={containerRef}
      className="relative flex-1 h-full w-full bg-[#0a0a0d] overflow-hidden flex items-start justify-start cursor-crosshair select-none"
      onMouseUp={handlePointerUp}
      onMouseLeave={handlePointerUp}
    >
      <canvas
        id="life-canvas"
        ref={canvasRef}
        className="block border border-[#3c3c46]/60 shadow-lg"
        onMouseDown={handlePointerDown}
        onMouseMove={handlePointerMove}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handlePointerUp}
      />
    </div>
  );
};
