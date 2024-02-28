import { CSSProperties } from "react";
import { generateFullLongShadow } from "../../lib/textShadow";
import { Text } from "../../lib/types";

function formatTextShadow(textShadow: any) {
  return `${textShadow.x || 0}px ${textShadow.y || 0}px ${
    textShadow.blur || 0
  }px ${textShadow.color || "black"}`;
}

const DEFAULT_TEXT_PROPERTIES = {
  rotation: 0,
  fontFamily: "Arial",
  fontSize: 16,
  fontWeight: 400,
  color: "white",
  backgroundColor: "transparent",
};

interface TextAssetProps {
  text: Text;
}

export default function SubtitleWord(props: TextAssetProps) {
  const { text } = props;

  const textProperties = {
    ...DEFAULT_TEXT_PROPERTIES,
    ...text,
  };

  let textShadow = "";
  let filterTextShadow = "";
  if (textProperties.longShadow && textProperties.longShadow.width > 0) {
    textShadow = `${generateFullLongShadow(
      textProperties.longShadow.width,
      textProperties.longShadow.color
    )}`;
  }

  if (textProperties.textShadow && textProperties.textShadow.blur > 0) {
    filterTextShadow = formatTextShadow(textProperties.textShadow);
  }

  const containerStyles: CSSProperties = {
    minWidth: "fit-content",
    minHeight: "fit-content",
    position: "relative",
    // height: `${textProperties.height * pixelScaleFactor}px`,

    // display: "flex",
    // alignItems: "center",
    // justifyContent: "center",
    // flex: 1,
  };

  const isGradient = textProperties.color.includes("gradient");

  const textStyles: CSSProperties = {
    backgroundColor: isGradient ? "transparent" : textProperties.color,
    backgroundImage: isGradient ? textProperties.color : "none",
    font: `${textProperties.fontWeight} ${textProperties.fontSize}px ${textProperties.fontFamily}`,
    WebkitTextFillColor: "transparent",
    WebkitBackgroundClip: "text",
    backgroundClip: "text", // Standard property, as a fallback
    backgroundSize: "cover",
    filter: `drop-shadow(${filterTextShadow})`,
    margin: 0,
    position: "absolute",
    letterSpacing: `${textProperties.letterSpacing}px`,
  };

  const shadowStyles: CSSProperties = {
    ...textStyles,
    backgroundImage: "none",
    color: "transparent",
    WebkitTextFillColor: "", // Remove the transparent fill
    WebkitBackgroundClip: "", // Remove the background clip
    backgroundClip: "", // Standard property, as a fallback
    textShadow,
    backgroundColor: "transparent",
  };

  return (
    <div style={containerStyles}>
      <span style={shadowStyles}>{text.text}</span>
      <span style={textStyles}>{text.text}</span>
    </div>
  );
}
