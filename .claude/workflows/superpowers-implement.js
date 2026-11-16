export const meta = {
    name: 'superpowers-implement',
    description: 'Superpowers executing-plans in rounds until every step is ticked and the tests are green',
    phases: [{ title: 'Implement' }, { title: 'Verify' }],
}

const plan = String(typeof args === 'string' ? args : (args?.plan ?? '')).trim()
if (!plan) throw new Error('Pass the plan file, e.g. docs/superpowers/plans/2026-11-16-discount-codes.md')

const DONE = { type: 'object', required: ['changed_files', 'summary'],
    properties: { changed_files: { type: 'array', items: { type: 'string' } }, summary: { type: 'string' } } }
const STATUS = { type: 'object', required: ['open_steps', 'tests_passed', 'notes'],
    properties: { open_steps: { type: 'number' }, tests_passed: { type: 'boolean' }, notes: { type: 'string' } } }

let notes = ''
for (let round = 1; round <= 3; round++) {
    await agent(`Use the Skill tool to run superpowers:executing-plans on ${plan}, following
    superpowers:test-driven-development. Work through the unchecked steps in order, test first,
    and tick each step when it is done. You run unattended: do not ask the human anything.
    Stay on the current branch, never create a git worktree, never push, and stop when the plan
    is done instead of finishing the branch. ${notes}`,
        { label: `implement ${round}`, phase: 'Implement', schema: DONE })
    const s = await agent(`Read-only checker: do not edit files. Count the unchecked "- [ ]" steps
    in ${plan} and run npm test.`,
        { label: `verify ${round}`, phase: 'Verify', effort: 'low', schema: STATUS })
    log(`round ${round}: ${s?.open_steps ?? '?'} open steps, tests ${s?.tests_passed ? 'green' : 'red'}`)
    if (s && s.open_steps === 0 && s.tests_passed) return { status: 'done', rounds: round }
    notes = `Last check: ${s?.notes ?? 'no report'}`
}
return { status: 'stopped after 3 rounds', notes }
