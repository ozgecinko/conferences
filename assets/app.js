const talks = [
  {
    id: "llm-based-recommendation-systems",
    title: "LLM-Based Recommendation Systems: From Embeddings to Real Personalization",
    shortTitle: "LLM-Based Recommendation Systems",
    description:
      "How LLMs and embeddings can move recommendation systems from semantic similarity toward more useful personalization patterns.",
    event: "PyData London 2026",
    date: "June 5-7, 2026",
    location: "London, United Kingdom",
    topics: ["Recommendation Systems", "Large Language Models"],
    folder: "llm-based-recommendation-systems",
    pdf: "LLM Based Recommendation Systems - Ozge Cinko.pdf",
    pptx: "LLM Based Recommendation Systems - Ozge Cinko.pptx",
  },
  {
    id: "designing-memory",
    title: "Designing Memory for AI Applications in Python",
    shortTitle: "Designing Memory",
    description:
      "A practical memory layer for AI applications: what to store, how to retrieve it, and how to avoid common failure modes.",
    event: "PyCon Italia 2026",
    date: "May 27-30, 2026",
    location: "Bologna, Italy",
    topics: ["Large Language Models"],
    folder: "designing-memory",
    pdf: "Designing Memory for AI Applications in Python.pdf",
    pptx: "Designing Memory for AI Applications in Python.pptx",
    links: [
      {
        label: "Blog post",
        url: "https://medium.com/@ozgecinko/designing-memory-for-ai-applications-d0bc5f8bdadd",
      },
    ],
  },
  {
    id: "how-shazam-identifies-songs",
    title: "How Shazam Identifies Songs in 5 Seconds: Audio Fingerprinting with Python",
    shortTitle: "How Shazam Identifies Songs",
    description:
      "A concrete walk-through of audio fingerprinting: spectrograms, stable peaks, fingerprints, and matching short recordings.",
    event: "PyCon Italia 2026 / PyCon Netherlands 2025",
    date: "May 27-30, 2026 and October 16, 2025",
    location: "Bologna, Italy / Utrecht, Netherlands",
    topics: ["Algorithms"],
    folder: "how-shazam-identifies-songs",
    pdf: "How Shazam Identifies Songs in 5 Seconds_ Audio Fingerprinting with Python - Ozge Cinko.pdf",
    pptx: "How Shazam Identifies Songs in 5 Seconds_ Audio Fingerprinting with Python - Ozge Cinko.pptx",
    links: [
      {
        label: "Demo repository",
        url: "https://github.com/ozgecinko/mini-shazam",
      },
    ],
  },
  {
    id: "measuring-experiments-in-llms",
    title: "Measuring Experiments in LLMs: A/B Tests and Automated Testing",
    shortTitle: "Measuring Experiments in LLMs",
    description:
      "Practical ways to evaluate LLM features, from product experiments and A/B testing to automated regression checks.",
    event: "PyCon Lithuania 2026",
    date: "April 7-10, 2026",
    location: "Vilnius, Lithuania",
    topics: ["Large Language Models", "Experimentation"],
    folder: "measuring-experiments-in-llms",
    pdf: "Measuring Experiments in LLMs_ A_B Tests and Automated Testing - Kader Miyanyedi, Ozge Cinko.pdf",
    pptx: "Measuring Experiments in LLMs_ A_B Tests and Automated Testing - Kader Miyanyedi, Ozge Cinko.pptx",
    speakers: ["Kader Miyanyedi", "Ozge Cinko"],
    links: [
      {
        label: "Blog post",
        url: "https://pub.towardsai.net/evaluating-and-monitoring-llms-with-langfuse-a-b-testing-metrics-bddea6e51574",
      },
    ],
  },
  {
    id: "the-master-algorithm",
    title: "One Algorithm To Rule Them All",
    shortTitle: "One Algorithm To Rule Them All",
    description:
      "A lightning talk using the idea of a master algorithm as a practical lens for understanding machine learning systems.",
    event: "PyCon Lithuania 2026",
    date: "April 10, 2026",
    location: "Vilnius, Lithuania",
    topics: ["Algorithms", "Machine Learning"],
    folder: "the-master-algorithm",
    pdf: "One Algorithm To Rule Them All - Ozge Cinko.pdf",
    pptx: "One Algorithm To Rule Them All - Ozge Cinko.pptx",
  },
  {
    id: "building-mirror-of-erised",
    title: "Building Harry Potter's Mirror of Erised with Python and Generative AI",
    shortTitle: "Building Mirror of Erised",
    description:
      "A playful generative AI project combining user input, image generation, and Python application logic into an interactive demo.",
    event: "PyCon Sweden 2025",
    date: "October 30-31, 2025",
    location: "Stockholm, Sweden",
    topics: ["Generative AI", "Creative Coding"],
    folder: "building-mirror-of-erised",
    pdf: "Building Harry Potter's Mirror of Erised with Python and Generative AI.pdf",
    pptx: "Building Harry Potter's Mirror of Erised with Python and Generative AI.pptx",
  },
];

const state = {
  selectedId: talks[0].id,
  topic: "All",
  query: "",
};

const topicFilters = [
  "All",
  "Algorithms",
  "Machine Learning",
  "Recommendation Systems",
  "Generative AI",
  "Large Language Models",
  "Experimentation",
  "Creative Coding",
];

const cardsEl = document.querySelector("#talkCards");
const filtersEl = document.querySelector("#filters");
const searchEl = document.querySelector("#search");
const selectedMetaEl = document.querySelector("#selectedMeta");
const selectedTitleEl = document.querySelector("#selectedTitle");
const selectedDescriptionEl = document.querySelector("#selectedDescription");
const selectedTagsEl = document.querySelector("#selectedTags");
const selectedLinksEl = document.querySelector("#selectedLinks");
const slideViewerEl = document.querySelector("#slideViewer");
const fallbackLinkEl = document.querySelector("#fallbackLink");

function assetUrl(talk, fileName) {
  return encodeURI(`./${talk.folder}/${fileName}`);
}

function uniqueTopics() {
  return topicFilters;
}

function talkMatches(talk) {
  const searchable = [
    talk.title,
    talk.description,
    talk.event,
    talk.location,
    talk.date,
    ...(talk.topics || []),
    ...(talk.speakers || []),
  ]
    .join(" ")
    .toLowerCase();
  const topicMatch = state.topic === "All" || talk.topics.includes(state.topic);
  return topicMatch && searchable.includes(state.query.toLowerCase().trim());
}

function filteredTalks() {
  return talks.filter(talkMatches);
}

function renderFilters() {
  filtersEl.innerHTML = uniqueTopics()
    .map(
      (topic) => `
        <button class="filter-button ${topic === state.topic ? "active" : ""}" type="button" data-topic="${topic}">
          ${topic}
        </button>
      `,
    )
    .join("");
}

function renderCards() {
  const visibleTalks = filteredTalks();
  if (!visibleTalks.length) {
    cardsEl.innerHTML = `<div class="empty-state">No talks match this search.</div>`;
    return;
  }

  if (!visibleTalks.some((talk) => talk.id === state.selectedId)) {
    state.selectedId = visibleTalks[0].id;
  }

  cardsEl.innerHTML = visibleTalks
    .map(
      (talk) => `
        <button class="talk-card ${talk.id === state.selectedId ? "active" : ""}" type="button" data-talk-id="${talk.id}">
          <h3>${talk.shortTitle}</h3>
          <p>${talk.event} · ${talk.location}</p>
          <div class="card-meta">
            <span class="pill">${talk.date}</span>
            <span class="pill">${talk.topics[0]}</span>
          </div>
        </button>
      `,
    )
    .join("");
}

function renderSelectedTalk() {
  const talk = talks.find((item) => item.id === state.selectedId) || talks[0];
  const pdfUrl = assetUrl(talk, talk.pdf);
  const pptxUrl = assetUrl(talk, talk.pptx);
  const extraLinks = talk.links || [];

  selectedMetaEl.textContent = `${talk.event} · ${talk.location}`;
  selectedTitleEl.textContent = talk.title;
  selectedDescriptionEl.textContent = talk.description;
  selectedTagsEl.innerHTML = talk.topics
    .map((topic) => `<span class="tag">${topic}</span>`)
    .join("");

  selectedLinksEl.innerHTML = [
    `<a class="primary-link" href="${pdfUrl}" target="_blank" rel="noreferrer">Open PDF</a>`,
    `<a class="secondary-link" href="${pptxUrl}">Download PPTX</a>`,
    `<a href="./${talk.folder}/readme.md">Notes</a>`,
    ...extraLinks.map(
      (link) => `<a href="${link.url}" target="_blank" rel="noreferrer">${link.label}</a>`,
    ),
  ].join("");

  slideViewerEl.src = `${pdfUrl}#view=FitH`;
  fallbackLinkEl.href = pdfUrl;
}

function render() {
  renderFilters();
  renderCards();
  renderSelectedTalk();
}

filtersEl.addEventListener("click", (event) => {
  const button = event.target.closest("[data-topic]");
  if (!button) return;
  state.topic = button.dataset.topic;
  render();
});

cardsEl.addEventListener("click", (event) => {
  const button = event.target.closest("[data-talk-id]");
  if (!button) return;
  state.selectedId = button.dataset.talkId;
  render();
});

searchEl.addEventListener("input", (event) => {
  state.query = event.target.value;
  render();
});

render();
