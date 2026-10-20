# Liquid d1 agent skill

Drop-in skill for Claude Code, Codex, and other agent environments.

The skill gives a coding agent context on Liquid AI's d1 decision-model family:
the shared System One contract (Choice, Score, Noul), question design,
probabilities, hosted API integrations, and local inference.

## Choose a d1 model

| Model | Deployment | Inputs |
| --- | --- | --- |
| `d1` | Hosted; lower-priced option | Text, images |
| `d1-ultra` | Hosted; most capable option | Text, images |
| `d1-3B` | Open weights, 3.1B | Text, images |
| `d1-omni-600M` | Open weights, 587M | Text with images or audio |

See the [model overview](https://docs.liquid.ai/lfm/models/decision-models)
and [migration guide](https://docs.liquid.ai/guides/decision-model-guide).

## Access d1

- **Liquid direct:** `d1` or `d1-ultra` at
  `https://api.liquid.ai/decisions/v1/systemone`
- **Vercel AI Gateway:** `liquid/d1` or `liquid/d1-ultra` through AI SDK's
  decision API
- **OpenRouter:** `liquid/d1` or `liquid/d1-ultra` through the Decisions API
- **Local / self-hosted:** `d1-3B` or `d1-omni-600M` through Transformers,
  llama.cpp, or MLX; see
  [local inference](skills/liquid-d1/references/local-inference.md).

The dependency-free [request runner](skills/liquid-d1/scripts/d1.py) supports
hosted Liquid and compatible local HTTP servers. For a local llama.cpp server,
pass a request file containing `state` and `questions` (no hosted model ID):

```bash
LIQUID_BASE_URL=http://127.0.0.1:8080 LIQUID_API_KEY= \
  python3 skills/liquid-d1/scripts/d1.py request.json
```

Local servers can omit authentication. Set `LIQUID_API_KEY` if your server
requires a bearer token. The no-argument demo uses hosted `model: "d1"`;
`--models` requires a server implementing `GET /v1/models`.

## Installation

**Claude Code**

Once this is published to the `Liquid4All/liquid-d1-skills` marketplace repo:

```bash
claude plugin marketplace add Liquid4All/liquid-d1-skills
claude plugin install liquid-d1@liquid-ai
```

**Codex**

Add the repository as a marketplace source:

```bash
codex plugin marketplace add Liquid4All/liquid-d1-skills
codex plugin add liquid-d1@liquid-ai
```

Alternatively, open `/plugins` after adding the marketplace and install
**Liquid d1** there. Start a new chat before using it.

**Other agents**

```bash
npx skills add Liquid4All/liquid-d1-skills --skill liquid-d1
```

Choose your agent when prompted. Installation is project-local by default;
add `-g` to install globally.

**Manual**

Copy the entire `skills/liquid-d1/` directory, including `references/` and
`scripts/`, into your agent's skills directory (for Claude Code:
`.claude/skills/liquid-d1/` in the project, or `~/.claude/skills/liquid-d1/`
globally).

**Paste into your agent**

```text
Install the Liquid d1 skill. If you're in Claude Code, run
`claude plugin marketplace add Liquid4All/liquid-d1-skills`, then
`claude plugin install liquid-d1@liquid-ai`. If you're in Codex, run
`codex plugin marketplace add Liquid4All/liquid-d1-skills`, then
`codex plugin add liquid-d1@liquid-ai`. If you're in another agent, run
`npx skills add Liquid4All/liquid-d1-skills --skill liquid-d1` and select your agent.
Use one installation method. Then use the Liquid d1 skill when working on
this project.
```

Choose one installation method to avoid duplicate copies.

### Updates

Claude Code plugin:

```bash
claude plugin marketplace update liquid-ai
claude plugin update liquid-d1@liquid-ai
```

Codex marketplace:

```bash
codex plugin marketplace upgrade liquid-ai
```

Restart Claude Code or run `/reload-plugins`. For skills.sh installs, run
`npx skills update`. For manual copies, replace the whole directory.

## Example prompts

Naming the skill in the prompt works in any agent. With the Claude Code
plugin you can invoke `/liquid-d1:liquid-d1`; in Codex, use `$liquid-d1`.

Find where d1 fits in an existing codebase:

```text
Using the Liquid d1 skill, explore this project and find places where a
typed decision from d1 could replace fragile parsing, regex classification,
or a prompt-and-parse LLM call.
```

Let the agent experiment against the API. Create a key on the console's API
keys page and export it:

```text
Using the Liquid d1 skill, run some experiments with the key I've exported
to LIQUID_API_KEY. Propose changes based on the most promising results.
```

## Working with the agent

1. Talk it through first. Use the prompts above as a starting point.
2. Review the plan before implementing.
3. Keep questions and thresholds in one file. They are what humans most
   need to review, and agents are not great at writing questions on the first
   pass. Expect to edit them together.
4. Don't take the agent's assertions at face value. Ask it to run the
   representative cases and show the probabilities.

## Common issues

**The agent isn't using the skill.** In Claude Code, invoke
`/liquid-d1:liquid-d1`; in Codex, invoke `$liquid-d1`. In other agents, say
"use the Liquid d1 skill". If it still does not load,
confirm the installer targeted the agent you are using, then restart it.

**Routing isn't doing what you expect.** Check the questions and thresholds.
Thresholds set too high cause false negatives; too low, false positives. The
questions may also need to be more specific about what the criteria mean.

**Confidence thresholds everywhere.** If you only need the best option, take
the highest-probability choice. If you have a specific statistical rule in
mind, use the probabilities directly. Confidence describes how concentrated
the distribution is, nothing more.

**The agent invents request or response fields.** The skill is stale, or the
agent didn't read the live docs. Update the skill, and point it at
https://console.liquid.ai/docs.

**401 on every request.** Check that `LIQUID_API_KEY` is set in the environment
the agent is running in and that the key is valid.

**429 with `model_unavailable`.** No healthy inference target for the model
right now. This is not a quota problem; retry after a short wait.

## Files

```
liquid-d1-skills/
├── .agents/plugins/marketplace.json  Codex marketplace catalog
├── .claude-plugin/                   Claude plugin and marketplace manifests
├── plugin.json                       portable Agent Plugins manifest
└── skills/liquid-d1/
    ├── SKILL.md                      instructions the agent loads
    ├── references/
    │   ├── api.md                    API contract, limits, and errors
    │   ├── providers.md              Liquid, Vercel, and OpenRouter access
    │   ├── sdks.md                   curl, Python, and TypeScript usage
    │   └── local-inference.md        open weights, images, and audio
    └── scripts/
        └── d1.py                     stdlib-only request runner
```

## License

Skill code and documentation: [MIT](LICENSE) © 2026 Liquid AI.

The downloadable `d1-3B` and `d1-omni-600M` model weights use the
[LFM Open License](https://docs.liquid.ai/lfm/help/model-license).
