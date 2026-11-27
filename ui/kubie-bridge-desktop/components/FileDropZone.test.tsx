import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FileDropZone } from "./FileDropZone";

function makeFile(name: string, size: number) {
  return new File(["x".repeat(size)], name, { type: "text/x-python" });
}

function dropZone() {
  return screen.getByTestId("file-drop-zone");
}

describe("FileDropZone attaching a file", () => {
  it("attaches a file chosen by browsing", async () => {
    const onFileChange = vi.fn();
    render(<FileDropZone file={null} onFileChange={onFileChange} />);
    const file = makeFile("pipeline.py", 10);

    await userEvent.setup().upload(screen.getByLabelText("Attach file"), file);

    expect(onFileChange).toHaveBeenCalledWith(file);
  });

  it("attaches a dropped file", () => {
    const onFileChange = vi.fn();
    render(<FileDropZone file={null} onFileChange={onFileChange} />);
    const file = makeFile("pipeline.py", 10);

    fireEvent.drop(dropZone(), { dataTransfer: { files: [file] } });

    expect(onFileChange).toHaveBeenCalledWith(file);
  });

  it("attaches only the first file when several are dropped", () => {
    const onFileChange = vi.fn();
    render(<FileDropZone file={null} onFileChange={onFileChange} />);
    const first = makeFile("first.py", 10);
    const second = makeFile("second.py", 10);

    fireEvent.drop(dropZone(), { dataTransfer: { files: [first, second] } });

    expect(onFileChange).toHaveBeenCalledOnce();
    expect(onFileChange).toHaveBeenCalledWith(first);
  });
});

describe("FileDropZone drag-over feedback", () => {
  it("indicates readiness while a file is dragged over and clears it on drag leave", () => {
    render(<FileDropZone file={null} onFileChange={vi.fn()} />);

    fireEvent.dragEnter(dropZone(), { dataTransfer: { files: [] } });
    expect(dropZone()).toHaveAttribute("data-dragging", "true");

    fireEvent.dragLeave(dropZone(), { dataTransfer: { files: [] } });
    expect(dropZone()).not.toHaveAttribute("data-dragging", "true");
  });

  it("clears the readiness indication when the file is dropped", () => {
    render(<FileDropZone file={null} onFileChange={vi.fn()} />);

    fireEvent.dragEnter(dropZone(), { dataTransfer: { files: [] } });
    fireEvent.drop(dropZone(), { dataTransfer: { files: [makeFile("a.py", 1)] } });

    expect(dropZone()).not.toHaveAttribute("data-dragging", "true");
  });
});

describe("FileDropZone attached file display", () => {
  it("shows the attached file's name and human-readable size", () => {
    render(<FileDropZone file={makeFile("pipeline.py", 1536)} onFileChange={vi.fn()} />);

    expect(screen.getByText("pipeline.py")).toBeInTheDocument();
    expect(screen.getByText("1.5 KB")).toBeInTheDocument();
  });

  it("shows the new file in place of the previous one when replaced", () => {
    const { rerender } = render(
      <FileDropZone file={makeFile("old.py", 10)} onFileChange={vi.fn()} />
    );

    rerender(<FileDropZone file={makeFile("new.py", 10)} onFileChange={vi.fn()} />);

    expect(screen.getByText("new.py")).toBeInTheDocument();
    expect(screen.queryByText("old.py")).not.toBeInTheDocument();
  });
});
