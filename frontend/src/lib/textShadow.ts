export interface ITextShadow {
    setColor: (color: string) => void;
    getColor: () => string;
    toString: (fontScaleFactor: number) => string;
    getShadows: () => TextShadow[];
  }
  
  export class TextShadow implements ITextShadow {
    horizontalOffset: string;
    verticalOffset: string;
    blurRadius: string;
    color: string;
  
    constructor(str?: string) {
      this.horizontalOffset = "0px";
      this.verticalOffset = "0px";
      this.blurRadius = "0px";
      this.color = "";
  
      if (str) {
        this.parseShadow(str);
      }
    }
  
    getShadows() {
      return [this];
    }
  
    getColor(): string {
      return this.color;
    }
  
    isColor(str: string): boolean {
      const colorRegex =
        /(rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*(,\s*[0-9.]+\s*)?\))|(#[0-9A-Fa-f]{3,6})|(\b[a-zA-Z]+\b)/;
      return colorRegex.test(str);
    }
  
    isLength(str: string): boolean {
      const lengthRegex = /[-+]?\d+px/;
      return lengthRegex.test(str);
    }
  
    parseShadow(str: string) {
      const parts = str
        .split(/(?=rgba?\()|(?<=\))|(?=#)|(?<=px)\s+/g)
        .filter(Boolean);
  
      parts.forEach((part) => {
        if (this.isColor(part)) {
          this.color = part;
        } else if (this.isLength(part)) {
          if (this.horizontalOffset === "0px") {
            this.horizontalOffset = part;
          } else if (this.verticalOffset === "0px") {
            this.verticalOffset = part;
          } else {
            this.blurRadius = part;
          }
        }
      });
    }
  
    setHorizontalOffset(value: string) {
      this.horizontalOffset = value;
    }
  
    setVerticalOffset(value: string) {
      this.verticalOffset = value;
    }
  
    setBlurRadius(value: string) {
      this.blurRadius = value;
    }
  
    setColor(value: string) {
      this.color = value;
    }
  
    toString(fontScaleFactor = 1): string {
      const scale = (value: string) => {
        const pixelValue = parseInt(value, 10);
        return isNaN(pixelValue) ? value : `${pixelValue * fontScaleFactor}px`;
      };
  
      return `${scale(this.horizontalOffset)} ${scale(
        this.verticalOffset
      )} ${scale(this.blurRadius)} ${this.color}`;
    }
  
    toJSON() {
      return this.toString();
    }
  }
  
  export class TextShadowMulti implements ITextShadow {
    shadows: TextShadow[];
  
    constructor(shadows: TextShadow[]) {
      this.shadows = shadows;
    }
  
    getShadows() {
      return this.shadows;
    }
  
    setColor(color: string) {
      this.shadows.forEach((shadow) => shadow.setColor(color));
    }
  
    getColor(): string {
      return this.shadows[0].getColor();
    }
  
    toString(fontScaleFactor = 1): string {
      return this.shadows
        .map((shadow) => shadow.toString(fontScaleFactor))
        .join(", ");
    }
  
    toJSON() {
      return this.toString();
    }
  }
  
  export const DEFAULT_LONG_SHADOW_PIXELS = 12;
  export const DEFAULT_FULL_LONG_SHADOW_PIXELS = 10;
  
  export function generateFullLongShadow(
    maxPixels: number = DEFAULT_FULL_LONG_SHADOW_PIXELS,
    shadowColor: string
  ): TextShadowMulti {
    const shadows: TextShadow[] = [];
    for (const iMultiplier of [-1, 1]) {
      for (const jMultiplier of [-1, 1]) {
        for (let i = 0; i < maxPixels; i++) {
          for (let j = 0; j < maxPixels; j++) {
            if (i === 0 && j === 0) {
              continue;
            }
  
            shadows.push(
              new TextShadow(
                `${iMultiplier * i}px ${jMultiplier * j}px 0px ${shadowColor}`
              )
            );
          }
        }
      }
    }
    return new TextShadowMulti(shadows);
  }
  
  export function generateLongShadow(
    maxPixels: number = DEFAULT_LONG_SHADOW_PIXELS,
    shadowColor: string
  ): TextShadowMulti {
    const shadows: TextShadow[] = [];
    for (let i = 0; i < maxPixels; i++) {
      for (let j = 0; j < maxPixels; j++) {
        if (i === 0 && j === 0) {
          continue;
        }
  
        shadows.push(new TextShadow(`${i}px ${j}px 0px ${shadowColor}`));
      }
    }
    for (let i = 0; i < maxPixels; i++) {
      for (let j = 0; j < maxPixels; j++) {
        if (i === 0 && j === 0) {
          continue;
        }
  
        shadows.push(new TextShadow(`${i}px ${j}px 0px ${shadowColor}`));
      }
    }
    return new TextShadowMulti(shadows);
  }
  