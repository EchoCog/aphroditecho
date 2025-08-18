declare module "ml-matrix" {
  export class Matrix {
    constructor(rows: number | number[][] | Matrix, columns?: number);
    rows: number;
    columns: number;
    set(row: number, column: number, value: number): void;
    get(row: number, column: number): number;
    add(matrix: Matrix): Matrix;
    sub(matrix: Matrix): Matrix;
    mul(value: number): Matrix;
    mmul(matrix: Matrix): Matrix;
    transpose(): Matrix;
    inverse(): Matrix;
    norm(): number;
    to1DArray(): number[];
    map(callback: (value: number) => number): Matrix;
    static zeros(rows: number, columns: number): Matrix;
    static random(rows: number, columns: number): Matrix;
    static eye(rows: number, columns: number): Matrix;
    static columnVector(array: number[]): Matrix;
    static rowVector(array: number[]): Matrix;

    // Add eigenvalues method
    eigenvalues(): number[] | Array<{ re: number; im: number }>;
  }
}

declare module "ml-distance" {
  export namespace distance {
    export function euclidean(a: number[], b: number[]): number;
  }
  export const euclidean: (a: number[], b: number[]) => number;
}

declare module "hnswlib-node" {
  export class HierarchicalNSW {
    constructor(space: string, dimensions: number);
    init(maxElements: number, ef?: number, M?: number, seed?: number): void;
    addPoint(point: number[], id?: number): void;
    searchKnn(point: number[], k: number): { distances: number[]; neighbors: number[] };
    writeIndex(filePath: string): void;
    readIndex(filePath: string, maxElements: number): void;
  }
}
