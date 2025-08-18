
// Recursive Pattern Explorer
const patternExplorer = {
    init() {
        this.canvas = document.getElementById('pattern-canvas');
        if (!this.canvas) return;
        
        this.ctx = this.canvas.getContext('2d');
        this.patterns = {
            sierpinski: this.drawSierpinski,
            mandelbrot: this.drawMandelbrot,
            kochCurve: this.drawKochCurve
        };
        
        this.setupControls();
    },
    
    setupControls() {
        const patternSelect = document.getElementById('pattern-select');
        if (!patternSelect) return;
        
        Object.keys(this.patterns).forEach(key => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = key.charAt(0).toUpperCase() + key.slice(1);
            patternSelect.appendChild(option);
        });
        
        patternSelect.addEventListener('change', () => {
            const pattern = patternSelect.value;
            this.clearCanvas();
            this.patterns[pattern].call(this);
        });
        
        // Initialize with first pattern
        if (patternSelect.options.length > 0) {
            const firstPattern = patternSelect.options[0].value;
            this.patterns[firstPattern].call(this);
        }
    },
    
    clearCanvas() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    },
    
    drawSierpinski() {
        const drawTriangle = (x1, y1, x2, y2, x3, y3, depth) => {
            if (depth === 0) {
                this.ctx.beginPath();
                this.ctx.moveTo(x1, y1);
                this.ctx.lineTo(x2, y2);
                this.ctx.lineTo(x3, y3);
                this.ctx.closePath();
                this.ctx.stroke();
                return;
            }
            
            const midX1 = (x1 + x2) / 2;
            const midY1 = (y1 + y2) / 2;
            const midX2 = (x2 + x3) / 2;
            const midY2 = (y2 + y3) / 2;
            const midX3 = (x1 + x3) / 2;
            const midY3 = (y1 + y3) / 2;
            
            depth--;
            drawTriangle(x1, y1, midX1, midY1, midX3, midY3, depth);
            drawTriangle(midX1, midY1, x2, y2, midX2, midY2, depth);
            drawTriangle(midX3, midY3, midX2, midY2, x3, y3, depth);
        };
        
        const w = this.canvas.width;
        const h = this.canvas.height;
        drawTriangle(w/2, 10, 10, h-10, w-10, h-10, 6);
    },
    
    drawMandelbrot() {
        const maxIter = 100;
        const w = this.canvas.width;
        const h = this.canvas.height;
        
        const imageData = this.ctx.createImageData(w, h);
        const data = imageData.data;
        
        for (let x = 0; x < w; x++) {
            for (let y = 0; y < h; y++) {
                // Convert pixel coordinate to complex number
                const a = (x - w/2) * 4 / w;
                const b = (y - h/2) * 4 / h;
                
                let ca = a;
                let cb = b;
                let n = 0;
                
                // Check if point is in Mandelbrot set
                while (n < maxIter) {
                    const aa = a * a - b * b;
                    const bb = 2 * a * b;
                    
                    a = aa + ca;
                    b = bb + cb;
                    
                    if (a * a + b * b > 16) {
                        break;
                    }
                    
                    n++;
                }
                
                // Color the pixel based on number of iterations
                const pix = (x + y * w) * 4;
                const norm = n / maxIter;
                data[pix + 0] = Math.round(norm * 255); // R
                data[pix + 1] = Math.round(norm * 50);  // G
                data[pix + 2] = Math.round(norm * 150); // B
                data[pix + 3] = 255; // Alpha
            }
        }
        
        this.ctx.putImageData(imageData, 0, 0);
    },
    
    drawKochCurve() {
        const koch = (x1, y1, x2, y2, depth) => {
            if (depth === 0) {
                this.ctx.moveTo(x1, y1);
                this.ctx.lineTo(x2, y2);
                return;
            }
            
            const angle = Math.PI / 3; // 60 degrees
            const distX = x2 - x1;
            const distY = y2 - y1;
            
            const oneThirdX = x1 + distX / 3;
            const oneThirdY = y1 + distY / 3;
            
            const twoThirdX = x1 + 2 * distX / 3;
            const twoThirdY = y1 + 2 * distY / 3;
            
            const peakX = oneThirdX + Math.cos(angle - Math.atan2(distY, distX)) * distX / 3;
            const peakY = oneThirdY + Math.sin(angle - Math.atan2(distY, distX)) * distX / 3;
            
            koch(x1, y1, oneThirdX, oneThirdY, depth - 1);
            koch(oneThirdX, oneThirdY, peakX, peakY, depth - 1);
            koch(peakX, peakY, twoThirdX, twoThirdY, depth - 1);
            koch(twoThirdX, twoThirdY, x2, y2, depth - 1);
        };
        
        this.ctx.beginPath();
        const w = this.canvas.width;
        const h = this.canvas.height;
        
        // Draw Koch snowflake
        const startX = w * 0.2;
        const startY = h * 0.7;
        const sideLength = w * 0.6;
        
        const height = sideLength * Math.sin(Math.PI / 3);
        const x1 = startX;
        const y1 = startY;
        const x2 = startX + sideLength;
        const y2 = startY;
        const x3 = startX + sideLength / 2;
        const y3 = startY - height;
        
        this.ctx.beginPath();
        koch(x1, y1, x2, y2, 4);
        koch(x2, y2, x3, y3, 4);
        koch(x3, y3, x1, y1, 4);
        this.ctx.stroke();
    }
};

document.addEventListener('DOMContentLoaded', () => {
    patternExplorer.init();
});
