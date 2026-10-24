"use client";

import { useEffect, useState } from "react";

const teamMembers = [
  "Elvin Pineda",
  "Santiago Acosta Rodriguez",
  "Andres Ferrer",
];

const slides = [
  {
    title: "What is Kubie-Bridge?",
    text: "An agentic tool that makes Kubeflow pipelines usable for model trainers who aren't Kubeflow experts.",
  },
  {
    title: "The Problem",
    text: "Running a training job on Kubeflow means writing pipeline code, packaging components, and learning the platform first.",
  },
  {
    title: "Our Approach",
    text: "Upload a training script and describe what you want. A LangGraph agent builds the pipeline and runs it on Kubeflow for you.",
  },
  {
    title: "Tech Stack",
    text: "Next.js frontend, FastAPI backend, a LangGraph agent, and Kubeflow on the KSU data center.",
  },
];

const SLIDE_INTERVAL_MS = 5000;

function Slideshow() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % slides.length);
    }, SLIDE_INTERVAL_MS);
    return () => clearInterval(timer);
  }, []);

  const prev = () => setIndex((i) => (i - 1 + slides.length) % slides.length);
  const next = () => setIndex((i) => (i + 1) % slides.length);

  const slide = slides[index];

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="flex w-full items-center gap-4">
        <button
          type="button"
          onClick={prev}
          aria-label="Previous slide"
          className="shrink-0 rounded-full px-3 py-1 text-2xl text-zinc-500 transition-colors hover:bg-black/[.04] hover:text-black dark:hover:bg-white/[.06] dark:hover:text-zinc-50"
        >
          ‹
        </button>

        <div className="flex min-h-36 flex-1 flex-col justify-center text-center">
          <h2 className="text-2xl font-semibold text-black dark:text-zinc-50">
            {slide.title}
          </h2>
          <p className="mt-3 text-zinc-600 dark:text-zinc-400">{slide.text}</p>
        </div>

        <button
          type="button"
          onClick={next}
          aria-label="Next slide"
          className="shrink-0 rounded-full px-3 py-1 text-2xl text-zinc-500 transition-colors hover:bg-black/[.04] hover:text-black dark:hover:bg-white/[.06] dark:hover:text-zinc-50"
        >
          ›
        </button>
      </div>

      <div className="flex gap-2">
        {slides.map((s, i) => (
          <button
            key={s.title}
            type="button"
            onClick={() => setIndex(i)}
            aria-label={`Go to slide ${i + 1}`}
            aria-current={i === index ? "true" : undefined}
            className={`h-2.5 w-2.5 rounded-full transition-colors ${
              i === index
                ? "bg-black dark:bg-zinc-50"
                : "bg-zinc-300 hover:bg-zinc-400 dark:bg-zinc-700 dark:hover:bg-zinc-600"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

export default function LandingPage() {
  return (
    <div className="flex flex-1 items-center justify-center bg-zinc-50 px-4 py-12 dark:bg-black">
      <main className="flex w-full max-w-3xl flex-col items-center gap-10 rounded-2xl border border-black/[.08] bg-white p-8 sm:p-12 dark:border-white/[.145] dark:bg-zinc-950">
        <h1 className="text-4xl font-bold tracking-tight text-black dark:text-zinc-50">
          Kubie-Bridge
        </h1>

        <ul className="flex flex-wrap justify-center gap-3">
          {teamMembers.map((name) => (
            <li
              key={name}
              className="rounded-full border border-black/[.08] px-4 py-1.5 text-sm text-zinc-700 dark:border-white/[.145] dark:text-zinc-300"
            >
              {name}
            </li>
          ))}
        </ul>

        <div className="w-full">
          <Slideshow />
        </div>

        <a
          href="/chat"
          className="rounded-full bg-black px-6 py-2.5 font-medium text-white transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-black dark:hover:bg-zinc-200"
        >
          Get started
        </a>
      </main>
    </div>
  );
}
