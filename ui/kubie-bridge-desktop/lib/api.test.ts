import { afterEach, describe, expect, it, vi } from "vitest";
import { uploadFile } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("uploadFile", () => {
  it("PUTs the file with the session cookie so the API can authenticate it", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const file = new File(["print('hi')"], "pipeline.py");

    await uploadFile("http://localhost:8000/uploads/proj1", file);

    expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/uploads/proj1", {
      method: "PUT",
      body: file,
      credentials: "include",
    });
  });

  it("throws when the upload is rejected", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 413 })));

    await expect(
      uploadFile("http://localhost:8000/uploads/proj1", new File(["x"], "a.py"))
    ).rejects.toMatchObject({ status: 413 });
  });
});
