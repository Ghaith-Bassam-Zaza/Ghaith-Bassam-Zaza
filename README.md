<div align="center">

<img src="./portrait.svg" width="460" alt="Ghaith Zaza"/>

<img src="./stats.svg" width="620" alt="Contributions in the last year"/>

[portfolio](https://ghaith-bassam-zaza.github.io/portfolio/) &nbsp;·&nbsp;
[linkedin](https://www.linkedin.com/in/ghaith-zaza-95b1311b7/)

</div>

<img src="./hd-about.svg" width="620" alt="about"/>

> AI engineer in Dubai. Computer and Systems Engineering, then all the way into AI.<br>
> Autonomy is the easy half. Being trusted in production is the other one.

I build agentic systems: planners that decide what to do next, retrieval that<br>
gives them something true to work from, and evaluators that stop the bad runs<br>
before anyone sees them. Most of what I ship is the unglamorous part — the<br>
retries, the guardrails, the tracing you need at 2am.

<img src="./hd-stack.svg" width="620" alt="stack"/>

<samp>python &nbsp; fastapi &nbsp; langgraph &nbsp; rag &nbsp; pgvector &nbsp; postgres &nbsp; pytorch &nbsp; typescript &nbsp; next.js &nbsp; docker &nbsp; aws</samp>

<img src="./constellation.svg" width="620" alt="The stack, sized by how often I reach for it"/>

<img src="./hd-projects.svg" width="620" alt="projects"/>

**autonomous social media orchestrator** &nbsp;·&nbsp; <samp>python, langgraph, heygen</samp><br>
Trend research to published video with nobody in the loop. Pulls live signal from<br>
Google Trends, News and Brave Search, writes the script, grades it against its own<br>
evaluation pass, then renders an avatar video with cloned voice. 22 ms average API<br>
response on Neon and Railway.

**ai real estate sales agent** &nbsp;·&nbsp; <samp>python, llm, crm</samp><br>
Qualifies leads in conversation, books the meeting itself once a lead clears the<br>
bar, and writes the whole thread back to a custom CRM in real time. Admin dashboard<br>
for listings, services and pipeline.

**enterprise chatbot deployment engine** &nbsp;·&nbsp; <samp>python, pgvector, rag</samp><br>
Point it at your URLs and get a chatbot. Scrapes, chunks, embeds, answers through a<br>
re-ranked RAG pipeline. Multi-tenant with hard Bot ID isolation and a one-line<br>
embed snippet.

**digital twin for autonomous vehicles** &nbsp;·&nbsp; <samp>python, cnn, yolo</samp><br>
Graduation project, grade A. Simulated environment where perception runs on raw<br>
sensor data and the vehicle decides for itself.

These four are client and university work and aren't public. The<br>
[portfolio](https://ghaith-bassam-zaza.github.io/portfolio/) has writeups; the<br>
repositories below are what I can show source for.

<img src="./hd-pipeline.svg" width="620" alt="how i build"/>

<img src="./pipeline.svg" width="620" alt="The shape of an agent run"/>

Every agent I've shipped has this shape. The interesting edge is the one pointing<br>
backwards: an evaluator that can reject its own planner's work is the difference<br>
between a demo and something you can leave running. Fan the workers out, judge the<br>
result, send it round again if it isn't good enough.

<img src="./hd-stats.svg" width="620" alt="stats"/>

<div align="center">

<img src="./streak.svg" width="620" alt="Current and longest streak"/>

<img src="./langs.svg" width="620" alt="Top languages by bytes and by repo"/>

<img src="./year.svg" width="620" alt="The last year, one character per day"/>

<img src="./timeline.svg" width="620" alt="Public repositories over time"/>

</div>

<img src="./hd-colophon.svg" width="620" alt="about this page"/>

Nothing on this page is loaded from somebody else's server. The stat graphics are<br>
drawn from the GitHub API by [a scheduled action](.github/workflows/stats.yml),
committed as files, and redrawn once a day — so there is no badge service here that
can rate-limit, change its mind, or quietly disappear.

They move using SMIL inside the SVG, because GitHub strips `<script>` from READMEs.
The section headings are images for the neighbouring reason: GitHub strips CSS too,
so an image is the only way to get this page's own typeface onto it.

The portrait is a photograph pushed through a character ramp. The fifteen glyphs it
uses weren't picked by eye — every printable character was rendered in JetBrains
Mono and measured for ink coverage, then the ones landing closest to evenly spaced
steps were kept. A face is nearly all midtones, and that is exactly where a
hand-guessed ramp falls apart. The typeface is subset to only the characters each
graphic actually draws and inlined as base64, which is not only for looks: the
portrait's grid assumes an advance width of exactly 0.600 em, and a viewer whose
default monospace is narrower would see it squeezed.

Language totals cover public repositories only, and if the API can't return all of
them the chart isn't redrawn at all — a percentage of an incomplete total is just a
wrong number. `year.svg` uses the same ramp as the portrait, thresholded by quantile
rather than fixed cutoffs, so a quiet year still has contrast.
