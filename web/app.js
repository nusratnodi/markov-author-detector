// Front end for server.py. All the Markov work happens in Python;
// this file only sends requests and shows the answers.

const $ = (id) => document.getElementById(id);
const errorBox = $("error");

async function api(path, body) {
  const options = body === undefined
    ? {}
    : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  let response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new Error("Can't reach the server. Is server.py still running?");
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status}).`);
  return data;
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

// Disable a button while a request runs, and report any error.
async function busy(button, label, task) {
  const original = button.textContent;
  button.disabled = true;
  button.textContent = label;
  showError("");
  try {
    await task();
  } catch (err) {
    showError(err.message);
  } finally {
    button.disabled = false;
    button.textContent = original;
  }
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// Ranking list: best match first. Scores are log-probabilities (closer to 0 = more likely).
function renderRanking(ranking) {
  const best = ranking[0].score;
  const list = el("ol", "ranking");
  ranking.forEach(({ author, score }, i) => {
    const item = el("li");
    item.append(
      el("span", "place", `${i + 1}.`),
      el("span", "name", author),
      el("span", "score", score.toFixed(1)),
      el("span", "gap", i === 0 ? "best" : `${(score - best).toFixed(1)}`),
    );
    list.append(item);
  });
  const caption = el("p", "meta",
    "Score = log-probability of the passage under each author's model. Higher (closer to 0) means a closer match.");
  const wrap = el("div");
  wrap.append(list, caption);
  return wrap;
}

/* ---------- tabs ---------- */

const tabs = [...document.querySelectorAll('[role="tab"]')];

function selectTab(tab) {
  tabs.forEach((t) => {
    const selected = t === tab;
    t.setAttribute("aria-selected", selected);
    t.tabIndex = selected ? 0 : -1;
    $(t.getAttribute("aria-controls")).hidden = !selected;
  });
  showError("");
}

tabs.forEach((tab, i) => {
  tab.addEventListener("click", () => selectTab(tab));
  tab.addEventListener("keydown", (e) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    if (!step) return;
    const next = tabs[(i + step + tabs.length) % tabs.length];
    selectTab(next);
    next.focus();
  });
});
selectTab(tabs[0]);

/* ---------- 1. generate ---------- */

$("generate-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const author = document.querySelector('input[name="author"]:checked')?.value;
  const button = e.submitter || e.target.querySelector("button");
  busy(button, "Writing…", async () => {
    const data = await api("/api/generate", { author, sentences: Number($("sentences").value) });
    $("generated-text").textContent = data.text;
    $("generated-meta").textContent =
      `Generated in the style of ${data.author} · order ${data.order} (looks at the last ${data.order} words)`;
    $("generate-result").hidden = false;
  });
});

/* ---------- 2. detect pasted text ---------- */

const textArea = $("detect-text");

textArea.addEventListener("input", () => {
  const count = (textArea.value.match(/[A-Za-z]+(?:['’][A-Za-z]+)*/g) || []).length;
  $("word-count").textContent = `${count} word${count === 1 ? "" : "s"}`;
});

textArea.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) $("detect-form").requestSubmit();
});

$("detect-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const button = e.target.querySelector("button");
  busy(button, "Guessing…", async () => {
    const data = await api("/api/detect", { text: textArea.value });
    const result = $("detect-result");
    const verdict = el("p", "verdict", "Guess: ");
    verdict.append(el("strong", "", data.ranking[0].author));
    result.replaceChildren(verdict, renderRanking(data.ranking));
    result.hidden = false;
  });
});

/* ---------- 3. random unseen passage ---------- */

const tally = { right: 0, total: 0 };

$("random-btn").addEventListener("click", (e) => {
  busy(e.currentTarget, "Picking…", async () => {
    const data = await api("/api/random");
    const guess = data.ranking[0].author;
    const correct = guess === data.realAuthor;

    tally.total += 1;
    if (correct) tally.right += 1;
    $("tally").textContent = `This session: ${tally.right} / ${tally.total} correct`;

    // Passages are cut from the middle of the book, so mark where they were cut.
    const end = /[.!?]$/.test(data.passage) ? "" : "…";
    $("random-passage").textContent = `“…${data.passage}${end}”`;

    const verdict = el("p", "verdict", "Guess: ");
    verdict.append(
      el("strong", "", guess),
      el("span", `badge ${correct ? "good" : "bad"}`, correct ? "Correct" : `Wrong, it was ${data.realAuthor}`),
    );
    $("random-ranking").replaceChildren(verdict, renderRanking(data.ranking));
    $("random-result").hidden = false;
  });
});

/* ---------- 4. accuracy ---------- */

const percent = (x) => `${Math.round(x * 100)}%`;

$("accuracy-btn").addEventListener("click", (e) => {
  $("accuracy-status").textContent = "Training 3 model sets and testing every passage. This takes a few seconds the first time.";
  busy(e.currentTarget, "Running…", async () => {
    try {
      const { orders } = await api("/api/accuracy");
      const authors = Object.keys(orders[0].authors);
      const bestAverage = Math.max(...orders.map((o) => o.average));

      const table = $("accuracy-table");
      const head = el("tr");
      head.append(el("th", "", "Order"));
      authors.forEach((a) => head.append(el("th", "", a.split(" ").pop())));
      head.append(el("th", "", "Average"));
      const thead = el("thead");
      thead.append(head);

      const tbody = el("tbody");
      orders.forEach((o) => {
        const row = el("tr", o.average === bestAverage ? "best" : "");
        row.append(el("td", "", `${o.order}`));
        authors.forEach((a) => row.append(el("td", "", percent(o.authors[a]))));
        row.append(el("td", "avg", percent(o.average)));
        tbody.append(row);
      });
      table.replaceChildren(thead, tbody);

      $("accuracy-status").textContent = `Tested on ${orders[0].passages.toLocaleString()} unseen passages.`;
      $("accuracy-result").hidden = false;
    } catch (err) {
      $("accuracy-status").textContent = "";
      throw err;
    }
  });
});

/* ---------- start-up: authors and book list ---------- */

api("/api/info")
  .then(({ authors }) => {
    const chips = $("author-chips");
    authors.forEach(({ name }, i) => {
      const id = `author-${i}`;
      const input = Object.assign(el("input"), { type: "radio", name: "author", id, value: name, checked: i === 0 });
      const label = el("label", "", name);
      label.htmlFor = id;
      chips.append(input, label);
    });

    const books = $("books");
    authors.forEach(({ name, book }) => {
      const item = el("li");
      item.append(el("em", "", book), document.createTextNode(` (${name.split(" ").pop()})`));
      books.append(item);
    });
  })
  .catch((err) => showError(err.message));
