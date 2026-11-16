export const meta = {
    name: 'superpowers-spec-plan',
    description: 'Superpowers brainstorming and writing-plans as separate agents, each checked before the next',
    phases: [{ title: 'Design' }, { title: 'Plan' }, { title: 'Check' }],
}

const OUT = { type: 'object', required: ['artifact', 'summary'],
    properties: { artifact: { type: 'string' }, summary: { type: 'string' } } }
const VERDICT = { type: 'object', required: ['ok', 'problems'],
    properties: { ok: { type: 'boolean' }, problems: { type: 'array', items: { type: 'string' } } } }

const RULES = `You run unattended and cannot ask the human anything. Where the skill says to ask a
  question or wait for approval, pick the sensible answer, record it under an "## Assumptions"
  heading and carry on; the human approves later, outside this workflow. Follow CLAUDE.md.
  Stay on the current branch, never create a git worktree, never touch src/.`

// One phase: an agent runs the Superpowers skill, a read-only reviewer checks the result.
async function step(title, task, rubric) {
    let prompt = task
    for (let attempt = 1; attempt <= 2; attempt++) {
        const out = await agent(prompt, { label: `${title} #${attempt}`, phase: title, schema: OUT })
        if (!out) continue
        const v = await agent(`Read-only reviewer: do not edit files. Read ${out.artifact} and the
      other files under docs/superpowers/. Pass it only if: ${rubric}`,
            { label: `check ${title}`, phase: 'Check', effort: 'low', schema: VERDICT })
        if (v && v.ok) { log(`${title}: ${out.summary}`); return out }
        prompt = `${task}\nA reviewer rejected the last attempt: ${(v?.problems ?? ['no verdict']).join('; ')}`
    }
    throw new Error(`${title} failed its check twice; stopping before the next phase`)
}

const feature = typeof args === 'string' ? args : JSON.stringify(args)
const spec = await step('Design',
    `Use the Skill tool to run superpowers:brainstorming for this feature:\n${feature}\n${RULES}
  Write the design doc under docs/superpowers/specs/ with no TBD or TODO markers. Stop there:
  do not write the plan. Return the design doc's path.`,
    'it has an Assumptions heading; every behaviour has a testable acceptance criterion; no TBD or TODO')

const plan = await step('Plan',
    `Use the Skill tool to run superpowers:writing-plans for the design in ${spec.artifact}.\n${RULES}
  Save the plan under docs/superpowers/plans/. Stop once it is saved: skip the "which execution
  approach" question and execute nothing. Return the plan's path.`,
    'every step is a "- [ ]" checkbox naming an exact file; a failing-test step comes before the code it tests; contradicts nothing in the design; adds no dependencies')

return { design: spec.artifact, plan: plan.artifact,
    next: `Review both, write ${plan.artifact.replace(/\.md$/, '')}.APPROVED, then run /superpowers-implement` }
