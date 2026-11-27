const FACES = 6;

export function ProcessingCube() {
  return (
    <div
      data-testid="processing-cube"
      aria-hidden="true"
      className="flex h-24 items-center justify-center"
    >
      <div className="kubie-cube-scene motion-safe:animate-cube-hop">
        <div className="kubie-cube motion-safe:animate-cube-tumble">
          {Array.from({ length: FACES }, (_, i) => (
            <div key={i} className="kubie-cube-face" />
          ))}
        </div>
      </div>
    </div>
  );
}
