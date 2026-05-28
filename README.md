# Designing Memory for AI Applications in Python

Companion code for my talk at **PyCon Italia 2026**.

LLMs are stateless. Memory is an illusion built by your application
layer and most teams build it badly. This repo is the clean version of
the patterns from the talk: a small, dependency-free, **time-aware**
memory layer in Python, with the four most common failure modes and
their fixes.

- Blog post: [Medium Link](https://medium.com/@ozgecinko/designing-memory-for-ai-applications-d0bc5f8bdadd)
- Slides: [Slide Link](./slides/Designing%20Memory%20for%20AI%20Applications%20in%20Python.pdf)
- Reach me: [LinkedIn](https://www.linkedin.com/in/ozgecinko)

## Install

```bash
git clone https://github.com/ozgecinko/designing-memory-talk
cd memory-talk
pip install -e ".[dev]"
```

Requires Python 3.10+. The core has **zero runtime dependencies**
(standard library only). `pytest` is the only dev dependency.

## Run it

```bash
python examples/quickstart.py # end-to-end walkthrough
pytest # 24 tests, all green
```

## License

MIT - see [LICENSE](./LICENSE). Use it, learn from it, ship it.
